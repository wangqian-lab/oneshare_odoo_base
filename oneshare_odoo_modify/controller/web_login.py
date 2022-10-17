# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID, api
from odoo.http import request, Response
from odoo.addons.oneshare_utils.http import oneshare_json_success_resp, oneshare_json_fail_response
from odoo.addons.web.controllers.main import ensure_db


class WebLogin(http.Controller):
    @http.api_route('/api/v1/login', type='apijson', auth='none', cors='*', csrf=False)
    def _login(self, **kwargs):
        params = request.ApiJsonRequest
        login = params.get('login')
        password = params.get('password')
        if not login or not password:
            return oneshare_json_fail_response(msg='Login Parameter Is Missing')
        ensure_db()
        if not request.session.db:
            return oneshare_json_fail_response(msg='Database not found')
        db = request.session.db
        # res_users = odoo.registry(db)['res.users']
        uid = request.session.authenticate(db, login, password)
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
                                                         user_id.image_128.decode()) if user_id.image_128 else ""
        }
        request.session.modified = True
        request.session.rotate = False  # 强制不要删除旧的session文件,只是更新其文件即可
        return oneshare_json_success_resp(msg=ret)
