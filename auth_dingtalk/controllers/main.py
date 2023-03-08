import os
import json

import werkzeug
from odoo.http import request
from werkzeug.urls import url_decode
from odoo.addons.auth_oauth.controllers.main import OAuthLogin

# provider name to get
ENV_DINGTLAK_PROVIDER_NAME = os.getenv("ENV_DINGTLAK_PROVIDER_NAME", "dingtalk")


class OpenIDLogin(OAuthLogin):
    def list_providers(self):
        providers = super(OpenIDLogin, self).list_providers()

        for provider in providers:
            if provider["name"] == ENV_DINGTLAK_PROVIDER_NAME:
                return_url = request.httprequest.url_root + "auth_oauth/signin"
                params = dict(
                    response_type="code",
                    redirect_uri=return_url,
                    scope=provider["scope"],
                    state=json.dumps(self.get_state(provider)),
                    appid=provider["client_id"],
                    access_token="",
                )
                provider["auth_link"] = "%s?%s" % (
                    provider["auth_endpoint"],
                    werkzeug.urls.url_encode(params),
                )
        return providers
