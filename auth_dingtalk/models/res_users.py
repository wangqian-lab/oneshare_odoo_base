import logging
import os
from requests import Response as httpResponse
from typing import Optional
from odoo import api, models
from odoo.exceptions import AccessDenied

from odoo.addons.oneshare_utils import CloudProvider
from odoo.addons.oneshare_utils.dingtalk import DingTalkProvider

_logger = logging.getLogger(__name__)

ENV_DINGTLAK_PROVIDER_NAME = os.getenv("ENV_DINGTLAK_PROVIDER_NAME", "dingtalk")

dingTalkProvider = None


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if not oauth_provider or oauth_provider["name"] != ENV_DINGTLAK_PROVIDER_NAME:
            return super(ResUsers, self)._generate_signup_values(
                provider, validation, params
            )
        oauth_uid = validation["user_id"]
        email = validation.get("email", validation.get("unionid"))
        name = validation.get("nick", email)
        return {
            "name": name,
            "login": email,
            "email": email,
            "oauth_provider_id": provider,
            "oauth_uid": oauth_uid,
            "active": True,
        }

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if not oauth_provider or oauth_provider["name"] != ENV_DINGTLAK_PROVIDER_NAME:
            return super(ResUsers, self).auth_oauth(provider, params)
        # use code flow default
        code = params.get("code")
        if not code:
            raise AccessDenied()

        validation = self._dingtalk_get_userinfo_by_code(oauth_provider, code)
        # required check
        if not validation or not validation.get("user_info"):
            raise AccessDenied()
        else:
            validation.update(**validation.get("user_info"))
            # do mapping and save code to access_token for login
            validation["user_id"] = validation["unionid"]
            params["access_token"] = code
        # retrieve and sign in user
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return self.env.cr.dbname, login, code

    @staticmethod
    def _dingtalk_get_userinfo_by_code(provider, code):
        global dingTalkProvider
        if not dingTalkProvider:
            dingTalkProvider = CloudProvider(
                DingTalkProvider,
                client_id=provider["client_id"],
                client_secret=provider["client_secret"],
            )
            dingTalkProvider.open()
        try:
            resp: Optional[httpResponse] = dingTalkProvider.validate_by_code(code=code)
            if resp:
                return resp.json()
            return None
        except Exception as e:
            _logger.error("_dingtalk_get_userinfo_by_code error: {}".format(e))
            return None
