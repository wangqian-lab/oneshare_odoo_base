import logging
import secrets

import requests
from enum import Enum

from odoo import fields, models, tools, api

try:
    from jose import jwt
except ImportError:
    logging.getLogger(__name__).debug("jose library not installed")


class AuthOauthFlow(Enum):
    OAuth2 = "access_token"
    OpenIdConnectCode = "id_token_code"
    OpenIdConnectImplicit = "id_token"


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    flow = fields.Selection(
        [(AuthOauthFlow.OAuth2.value, "OAuth2"),
         (AuthOauthFlow.OpenIdConnectCode.value, "OpenID Connect (authorization code flow)"),
         (AuthOauthFlow.OpenIdConnectImplicit.value, "OpenID Connect (implicit flow, not recommended)")],
        string="Auth Flow",
        default=AuthOauthFlow.OAuth2.value,
    )
    token_map = fields.Char(
        help="Some Oauth providers don't map keys in their responses "
             "exactly as required.  It is important to ensure user_id and "
             "email at least are mapped. For OpenID Connect user_id is "
             "the sub key in the standard."
    )
    client_secret = fields.Char(
        help="Used in OpenID Connect authorization code flow for confidential clients.",
    )
    code_verifier = fields.Char(
        default=lambda self: secrets.token_urlsafe(32), help="Used for PKCE."
    )
    validation_endpoint = fields.Char(required=False)
    token_endpoint = fields.Char(
        string="Token URL", help="Required for OpenID Connect authorization code flow."
    )
    logout_endpoint = fields.Char(
        help="Logout Url for SSO.",
    )
    jwks_uri = fields.Char(string="JWKS URL", help="Required for OpenID Connect.")

    @tools.ormcache("self.jwks_uri", "kid")
    def _get_key(self, kid):
        r = requests.get(self.jwks_uri)
        r.raise_for_status()
        response = r.json()
        if "keys" not in response:
            return {}
        for key in response["keys"]:
            if key["kid"] == kid:
                return key
        return {}

    def _map_token_values(self, res):
        if self.token_map:
            for pair in self.token_map.split(","):  # 通过逗号分割
                from_key, to_key = [k.strip() for k in pair.split(":", 1)]
                if to_key not in res:
                    res[to_key] = res.get(from_key, "")
        return res

    def _parse_id_token(self, id_token, access_token):
        self.ensure_one()
        res = {}
        header = jwt.get_unverified_header(id_token)
        res.update(
            jwt.decode(
                id_token,
                self._get_key(header.get("kid")),
                algorithms=["RS256"],
                audience=self.client_id,
                access_token=access_token,
            )
        )

        res.update(self._map_token_values(res))
        return res
