# Copyright 2016 ICTSTUDIO <http://www.ictstudio.eu>
# Copyright 2021 ACSONE SA/NV <https://acsone.eu>
# License: AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import base64
import hashlib
import logging
import secrets

from http import HTTPStatus
import werkzeug
from odoo import http, tools
from werkzeug.urls import url_decode, url_encode
from odoo.addons.web.controllers.main import Session
from odoo.addons.auth_oauth.controllers.main import OAuthLogin, ensure_db, request
from odoo.addons.auth_oidc.models.auth_oauth_provider import AuthOauthFlow

from odoo.addons.auth_oauth.controllers.main import OAuthLogin

_logger = logging.getLogger(__name__)


class OpenIDLogin(OAuthLogin, Session):
    def list_providers(self):
        providers = super(OpenIDLogin, self).list_providers()
        for provider in providers:
            _flow = provider.get("flow")
            if not _flow:
                continue
            flow = AuthOauthFlow(_flow)
            if flow in (
                AuthOauthFlow.OpenIdConnectCode,
                AuthOauthFlow.OpenIdConnectImplicit,
            ):
                params = url_decode(provider["auth_link"].split("?")[-1])
                # nonce
                params["nonce"] = secrets.token_urlsafe()
                # response_type
                if flow == AuthOauthFlow.OpenIdConnectImplicit:
                    # #ImplicitAuthRequest
                    params["response_type"] = "id_token token"
                elif flow == AuthOauthFlow.OpenIdConnectCode:
                    params["response_type"] = "code"
                # PKCE (https://tools.ietf.org/html/rfc7636)
                code_verifier = provider["code_verifier"]
                code_challenge = base64.urlsafe_b64encode(
                    hashlib.sha256(code_verifier.encode("ascii")).digest()
                ).rstrip(b"=")
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"
                # scope
                if provider.get("scope"):
                    if "openid" not in provider["scope"].split():
                        _logger.error("openid connect scope must contain 'openid'")
                    params["scope"] = provider["scope"]
                # auth link that the user will click
                provider[
                    "auth_link"
                ] = f"{provider.get('auth_endpoint')}?{url_encode(params)}"
        return providers

    def get_sso_provider(self):
        providers = self.list_providers()
        icp = request.env["ir.config_parameter"].sudo()
        sso_provider = icp.get_param("sso.provider")
        sso_enabled = icp.get_param("sso.enabled")
        if not sso_enabled:
            return False, None
        elif isinstance(sso_enabled, str) and sso_enabled.lower() in (
            "false",
            "f",
            "no",
            "0",
        ):
            return False, None
        for provider in providers:
            if provider.get("name") == sso_provider and provider.get("auth_link"):
                return True, provider
        return False, None

    @http.route()
    def web_client(self, s_action=None, **kw):
        ret = super(OpenIDLogin, self).web_client(s_action, **kw)
        sso_enable, provider = self.get_sso_provider()
        if not sso_enable or not provider:
            return ret
        auth_link = (
            provider.get("auth_link") if provider.get("auth_link") else "/web/login"
        )
        if not request.session.uid:
            return werkzeug.utils.redirect(auth_link, HTTPStatus.SEE_OTHER)
        return ret

    @http.route()
    def logout(self, redirect="/web"):
        # 先退出oauth登录 否则导致session删除拿不到token无法退出三方登录系统
        sso_enabled, provider = self.get_sso_provider()
        if sso_enabled and provider:
            request.env["res.users"].sudo().logout(provider)
        return super(OpenIDLogin, self).logout(redirect)
