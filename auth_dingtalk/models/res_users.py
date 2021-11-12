import json
import base64
import hashlib
import logging
import time
import hmac
import os
import requests

from odoo import api, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

ENV_DINGTLAK_PROVIDER_NAME = os.getenv('ENV_DINGTLAK_PROVIDER_NAME', 'dingtalk')


def sign(secret, timestamp):
    """
    钉钉api签名函数
    :param secret: 钉钉app的secret
    :param timestamp: 目前时间戳
    :return: app的secret对时间戳进行sha256加密并base64的结果
    """
    msg = timestamp
    signature = hmac.new(secret.encode('utf-8'), msg.encode('utf-8'), digestmod=hashlib.sha256).digest()

    return base64.b64encode(signature)


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        if provider != ENV_DINGTLAK_PROVIDER_NAME:
            return super(ResUsers, self)._generate_signup_values(provider, validation, params)
        oauth_uid = validation['user_id']
        email = validation.get('email', validation.get('unionid'))
        name = validation.get('nick', email)
        return {
            'name': name,
            'login': email,
            'email': email,
            'oauth_provider_id': provider,
            'oauth_uid': oauth_uid,
            'active': True,
        }

    @api.model
    def auth_oauth(self, provider, params):
        if provider != ENV_DINGTLAK_PROVIDER_NAME:
            return super(ResUsers, self).auth_oauth(provider, params)
        # use code flow default
        code = params.get("code")
        if not code:
            raise AccessDenied()
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)

        validation = self._dingtalk_get_userinfo_by_code(oauth_provider, code)
        # required check
        if not validation or not validation.get("user_info"):
            raise AccessDenied()
        else:
            validation.update(**validation.get("user_info"))
            # do mapping and save code to access_token for login
            validation['user_id'] = validation['unionid']
            params['access_token'] = code
        # retrieve and sign in user
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return self.env.cr.dbname, login, code

    @staticmethod
    def _dingtalk_get_userinfo_by_code(provider, code):
        # https://developers.dingtalk.com/document/app/queries-basic-user-information
        timestamp = str(int(time.time() * 1e3))
        try:
            query = {
                "accessKey": provider["client_id"],  # appId
                "timestamp": timestamp,
                "signature": sign(provider["client_secret"], timestamp)
            }
            resp = requests.post(provider['validation_endpoint'], params=query, json={
                "tmp_auth_code": code,
            })
            return json.loads(resp.text)
        except Exception as e:
            _logger.error("get_userinfo_by_code got error: {}".format(e))
            return None
