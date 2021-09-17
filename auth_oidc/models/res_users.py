import requests

from odoo import api, models, _
from odoo.tools import ustr
from odoo.exceptions import AccessDenied
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.http import request
from ast import literal_eval
from distutils.util import strtobool
import os

ENV_ONESHARE_SIGNUP_PUBLIC_USER = strtobool(os.getenv('ENV_ONESHARE_SIGNUP_PUBLIC_USER', 'False'))


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _signup_create_user(self, values):
        if ENV_ONESHARE_SIGNUP_PUBLIC_USER:
            return self._create_user_from_public_user(values)
        return super(ResUsers, self)._signup_create_user(values)

    def _create_user_from_public_user(self, values):
        template_user_id = literal_eval(
            self.env['ir.config_parameter'].sudo().get_param('base.template_public_user_id', 'False'))
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_('Signup: invalid public user'))

        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
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
                redirect_uri=redirect_uri
            ),
            auth=auth,
        )
        response.raise_for_status()
        response_json = response.json()
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
            raise AccessDenied()
        if not id_token:
            raise AccessDenied()
        validation = oauth_provider.parse_id_token(id_token, access_token)
        # required check
        if not validation.get("user_id"):
            raise AccessDenied()
        # retrieve and sign in user
        params["access_token"] = access_token
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return self.env.cr.dbname, login, access_token
