import requests

from odoo import api, models
from odoo.exceptions import AccessDenied
from odoo.http import request


class ResUsers(models.Model):
    _inherit = "res.users"

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
