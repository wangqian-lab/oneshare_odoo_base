import requests

from odoo import api, models, _
from odoo.tools import ustr
from odoo.exceptions import AccessDenied
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.http import request
from ast import literal_eval
from distutils.util import strtobool
import os
import logging

_logger = logging.getLogger(__name__)

ENV_ONESHARE_SIGNUP_PUBLIC_USER = strtobool(
    os.getenv("ENV_ONESHARE_SIGNUP_PUBLIC_USER", "False")
)
ENV_ONESHARE_REALM_ROLE_KEY = os.getenv("ENV_ONESHARE_REALM_ROLE_KEY", "role")


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _signup_create_user(self, values):
        if hasattr(self, "context"):
            context = self.context
            force_portal_user = context.get("force_portal_user", False)
            if ENV_ONESHARE_SIGNUP_PUBLIC_USER and not force_portal_user:
                return self._create_user_from_public_user(values)
        return super(ResUsers, self)._signup_create_user(values)

    def _create_user_from_public_user(self, values):
        template_user_id = literal_eval(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base.template_public_user_id", "False")
        )
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_("Signup: invalid public user"))

        if not values.get("login"):
            raise ValueError(_("Signup: no login given for new user"))
        if not values.get("partner_id") and not values.get("name"):
            raise ValueError(_("Signup: no name or partner given for new user"))

        # create a copy of the template user (attached to a specific partner_id if given)
        values["active"] = True
        try:
            with self.env.cr.savepoint():
                return template_user.with_context(no_reset_password=True).copy(values)
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))

    @staticmethod
    def _auth_oauth_get_tokens_implicit_flow(oauth_provider, params):
        return params.get("access_token"), params.get("id_token")

    @staticmethod
    def _auth_oauth_get_tokens_auth_code_flow(oauth_provider, params):
        code = params.get("code")
        auth = None
        redirect_uri = request.httprequest.url_root + "auth_oauth/signin"
        if oauth_provider.client_secret:
            auth = (oauth_provider.client_id, oauth_provider.client_secret)
        response = requests.post(
            oauth_provider.token_endpoint,
            data=dict(
                client_id=oauth_provider.client_id,
                grant_type="authorization_code",
                code=code,
                code_verifier=oauth_provider.code_verifier,
                redirect_uri=redirect_uri,
            ),
            auth=auth,
        )
        response.raise_for_status()
        response_json = response.json()
        # 将refresh_token存在odoo session
        if response_json.get("refresh_token"):
            request.httprequest.session["refresh_token"] = response_json.get(
                "refresh_token"
            )
        return response_json.get("access_token"), response_json.get("id_token")

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if oauth_provider.flow == "id_token":
            access_token, id_token = self._auth_oauth_get_tokens_implicit_flow(
                oauth_provider, params
            )
        elif oauth_provider.flow == "id_token_code":
            access_token, id_token = self._auth_oauth_get_tokens_auth_code_flow(
                oauth_provider, params
            )
        else:
            return super(ResUsers, self).auth_oauth(provider, params)
        if not access_token:
            _logger.error("No access_token in response.")
            raise AccessDenied()
        if not id_token:
            _logger.error("No id_token in response.")
            raise AccessDenied()
        validation = oauth_provider._parse_id_token(id_token, access_token)
        # required check
        if not validation.get("user_id"):
            _logger.error("user_id claim not found in id_token (after mapping).")
            raise AccessDenied()
        # retrieve and sign in user
        params["access_token"] = access_token
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # ensure and solve role
        self._ensure_and_solve_role(validation, login, provider)
        # return user credentials
        return self.env.cr.dbname, login, access_token

    @api.model
    def logout(self, oauth_provider):
        auth = None
        client_secret = oauth_provider.get("client_secret")
        client_id = oauth_provider.get("client_id")
        if client_secret and client_id:
            auth = (oauth_provider.get("client_id"), client_secret)
        session = request.httprequest.session
        if session.get("refresh_token"):
            requests.post(
                oauth_provider.get("logout_endpoint"),
                data=dict(
                    refresh_token=session.get("refresh_token"),
                ),
                auth=auth,
            )

    def _ensure_and_solve_role(self, validation, login, provider):
        """
        这个方法调用在登录或者注册时，如果id_token包含了用户的角色，且角色可以在odoo角色mapping里找到，则重新赋予用户角色。

        :param validation: id_token包含的信息
        :param login: 用户email
        :param provider: oauth provider
        :return:
        """
        roles = validation.get(ENV_ONESHARE_REALM_ROLE_KEY)
        if not login:
            return
        if roles and isinstance(roles, list):
            try:
                oauth_uid = validation["user_id"]
                oauth_user = self.search(
                    [
                        ("oauth_uid", "=", oauth_uid),
                        ("oauth_provider_id", "=", provider),
                    ]
                )
                if not oauth_user:
                    raise AccessDenied()
                if len(oauth_user) != 1:
                    raise AssertionError
                role_line_ids = self.env["res.users.role"]
                role_line_obj = self.env["res.users.role.line"]
                # roles: ["admin", "demo", ...]
                for role in roles:
                    res_role = (
                        self.env["res.users.role"].sudo().search([("name", "=", role)])
                    )
                    if not res_role:
                        continue
                    domain = [
                        ("role_id", "=", res_role.id),
                        ("user_id", "=", oauth_user.id),
                        ("is_enabled", "=", True),
                    ]
                    role_line = role_line_obj.sudo().search(domain)
                    if not role_line:
                        role_line = role_line_obj.sudo().create(
                            {
                                "role_id": res_role.id,
                                "user_id": oauth_user.id,
                                "is_enabled": True,
                            }
                        )
                    role_line_ids += role_line
                oauth_user.write(
                    {"role_line_ids": [(6, 0, role_line_ids.ids)]}
                )  # 强制替换角色组
            except Exception as e:
                _logger.error(f"_ensure_and_solve_role error: {ustr(e)}")
                pass
