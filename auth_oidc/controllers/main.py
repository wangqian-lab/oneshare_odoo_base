import base64
import hashlib
import secrets

import requests
import werkzeug
from odoo import http, tools
from odoo.exceptions import AccessError
from werkzeug.urls import url_decode, url_encode

from odoo.addons.auth_oauth.controllers.main import OAuthLogin, ensure_db, request
from odoo.addons.auth_oidc.models.auth_oauth_provider import AuthOauthFlow


DefaultProviderName = "KeyCloak"


class OpenIDLogin(OAuthLogin):

    def __init__(self, *args, **kwargs):
        icp = request.env['ir.config_parameter'].sudo()
        oidc_provider_default = icp.get_param('oidc_provider_default')
        if not oidc_provider_default:
            icp.set_param('oidc_provider_default', DefaultProviderName)
        super(OpenIDLogin, self).__init__(*args, **kwargs)

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
                provider["auth_link"] = f"{provider.get('auth_endpoint')}?{url_encode(params)}"
        return providers

    def get_default_provider(self):
        providers = self.list_providers()
        icp = request.env['ir.config_parameter'].sudo()
        oidc_provider_default = icp.get_param("oidc_provider_default")
        for provider in providers:
            if provider.get("name") == oidc_provider_default and provider.get("auth_link"):
                return provider
        return None

    @http.route()
    def web_client(self, s_action=None, **kw):
        ensure_db()
        provider = self.get_default_provider()

        auth_link = provider.get("auth_link") if provider.get("auth_link") else "/web/login"
        if not request.session.uid:
            return werkzeug.utils.redirect(auth_link, 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        return super(OpenIDLogin, self).web_client(s_action, **kw)

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        # 先退出oauth登录
        provider = self.get_default_provider()
        request.env['res.users'].sudo().logout(provider)

        # 再删除cookie
        request.session.logout(keep_db=True)
        return werkzeug.utils.redirect(redirect, 303)
