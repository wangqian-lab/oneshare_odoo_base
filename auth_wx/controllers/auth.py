# -*- coding: utf-8 -*-
import os
from odoo import http, api
from odoo.http import request
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.oneshare_utils.http import oneshare_json_success_resp, oneshare_json_fail_response
from odoo.addons.oneshare_utils.wechat import WechatProvider
from odoo.addons.oneshare_utils import CloudProvider

ENV_WECHAT_APP_ID = os.getenv('ENV_WECHAT_APP_ID', '')
ENV_WECHAT_SECRET_KEY = os.getenv('ENV_WECHAT_SECRET_KEY', '')


class AuthWx(http.Controller):

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        oauth_uid = validation['user_id']
        email = validation.get('email', 'provider_%s_user_%s' % (provider, oauth_uid))
        name = validation.get('name', email)
        return {
            'name': name,
            'login': email,
            'email': email,
            'oauth_uid': oauth_uid,
            'oauth_access_token': params['access_token'],
            'active': True,
        }

    def wechat_login(self, open_id, session_key):
        try:
            need_user_additional_info = False
            res_user_obj = request.env['res.users'].sudo()
            wx_user = res_user_obj.search([("oauth_uid", "=", open_id)])
            if not wx_user:
                raise AccessDenied()
            assert len(wx_user) == 1
            wx_user.write({'oauth_access_token': session_key})
            return wx_user.login, need_user_additional_info
        except AccessDenied as access_denied_exception:
            # 没有相关用户，需要重新创建
            need_user_additional_info = True
            validation = {
                'user_id': open_id,
            }
            params = {
                'access_token': session_key
            }
            values = self._generate_signup_values('wxapp', validation, params)
            try:
                # session_key 作为signup token, 微信强制创建的是portal用户
                _, login, _ = res_user_obj.with_context({'force_portal_user': True}).signup(values, None)
                return login, need_user_additional_info
            except (SignupError, UserError) as e:
                raise access_denied_exception

    @http.api_route('/api/v1/auth/<string:provider>', type='apijson', auth='none', cors='*', csrf=False)
    def wechat_app_login(self, provider, *args, **kw):
        params = request.ApiJsonRequest
        cr = request.env.cr
        ICP = request.env['ir.config_parameter'].sudo()
        if provider != 'wxapp':
            return oneshare_json_fail_response(msg=f'{provider}不支持')
        wx_code = params.get('code')
        if not wx_code:
            return oneshare_json_fail_response(msg='微信code为空')
        wx_app_id = ICP.get_param('wxapp.app_id', ENV_WECHAT_APP_ID)
        wx_app_secret = ICP.get_param('wxapp.app_secret', ENV_WECHAT_SECRET_KEY)
        WechatClient = CloudProvider(WechatProvider, app_id=wx_app_id, secret_key=wx_app_secret)
        resp = WechatClient.auth(code=wx_code)
        if not resp:
            return oneshare_json_fail_response(msg='微信认证错误!!!')
        db = request.session.db
        open_id = resp.get('openid')
        session_key = resp.get('session_key')
        login, need_user_additional_info = self.wechat_login(open_id, session_key)
        cr.commit()
        uid = request.session.authenticate(db, login, session_key)
        if not uid:
            return oneshare_json_fail_response(msg='User Auth Fail')
        user_id = request.env['res.users'].sudo().browse(uid)
        if not user_id:
            return oneshare_json_fail_response(msg='User Access Deny')
        ret = {
            'id': user_id.id,
            'database': db,
            'name': user_id.name,
            'login': user_id.login,
            'status': 'active' if user_id.active else 'inactive',
            'token': request.session.session_token,
            'session_id': request.session.sid,
            'image_small': u'data:{0};base64,{1}'.format('image/png',
                                                         user_id.image_128.decode()) if user_id.image_128 else "",
            'need_user_additional_info': need_user_additional_info,
            'groups': user_id.groups_id.mapped('name'),  # fixme:可能存在性能风险
        }
        request.session.modified = True
        request.session.rotate = False  # 强制不要删除旧的session文件,只是更新其文件即可
        return oneshare_json_success_resp(msg=ret)
