import base64
import hashlib
import secrets

from werkzeug.urls import url_decode, url_encode

from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.auth_oidc.models.auth_oauth_provider import AuthOauthFlow


class OpenIDLogin(OAuthLogin):
    def list_providers(self):
        providers = super(OpenIDLogin, self).list_providers()
        for provider in providers:
            flow = AuthOauthFlow(provider.get("flow"))
            if flow in (AuthOauthFlow.OpenIdConnectCode, AuthOauthFlow.OpenIdConnectImplicit):
                params = url_decode(provider["auth_link"].split("?")[-1])
                # nonce
                params["nonce"] = secrets.token_urlsafe()
                # response_type
                if flow == AuthOauthFlow.OpenIdConnectImplicit:
                    # #ImplicitAuthRequest
                    params["response_type"] = "id_token token"
                elif flow == AuthOauthFlow.OpenIdConnectCode:
                    params["response_type"] = "code"

                code_verifier = provider["code_verifier"]
                code_challenge = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode("ascii")).digest()
                ).rstrip(b"=")
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"
                # scope
                if provider.get("scope"):
                    if "openid" not in provider["scope"].split():
                        raise Exception("openid connect scope must contain 'openid'")
                    params["scope"] = provider["scope"]
                # auth link that the user will click
                provider["auth_link"] = "{}?{}".format(
                    provider["auth_endpoint"], url_encode(params)
                )
        return providers
