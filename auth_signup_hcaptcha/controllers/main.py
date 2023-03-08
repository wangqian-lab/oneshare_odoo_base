# -*- coding: utf-8 -*-


from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo import http
import logging
import requests

from odoo import api, models, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class AuthSignup(AuthSignupHome):
    @api.model
    def _verify_hcaptcha_token(self, ip_addr, token, action=False):
        private_key = (
            request.env["ir.config_parameter"].sudo().get_param("hcaptcha_private_key")
        )
        public_key = (
            request.env["ir.config_parameter"].sudo().get_param("hcaptcha_public_key")
        )
        if not private_key:
            return "no_secret"
        try:
            r = requests.post(
                "https://hcaptcha.com/siteverify",
                {
                    "secret": private_key,
                    "response": token,
                    "remoteip": ip_addr,
                    "sitekey": public_key,
                },
                timeout=2,
            )  # it takes ~50ms to retrieve the response
            result = r.json()
            res_success = result["success"]
            res_action = res_success and action
        except requests.exceptions.Timeout:
            logger.error(
                "Trial captcha verification timeout for ip address %s", ip_addr
            )
            return "timeout"
        except Exception:
            logger.error("Trial captcha verification bad request response")
            return "bad_request"

        if res_success:
            score = result.get("score", False)
            if res_action and res_action != action:
                logger.warning(
                    "Trial captcha verification for ip address %s failed with action %f, expected: %s.",
                    ip_addr,
                    score,
                    action,
                )
                return "wrong_action"
            logger.info(
                "Trial captcha verification for ip address %s succeeded with score %f.",
                ip_addr,
                score,
            )
            return "is_human"
        errors = result.get("error-codes", [])
        logger.warning(
            "Trial captcha verification for ip address %s failed error codes %r. token was: [%s]",
            ip_addr,
            errors,
            token,
        )
        for error in errors:
            if error in ["missing-input-secret", "invalid-input-secret"]:
                return "wrong_secret"
            if error in ["missing-input-response", "invalid-input-response"]:
                return "wrong_token"
            if error == "timeout-or-duplicate":
                return "timeout"
            if error == "bad-request":
                return "bad_request"
        return "is_bot"

    @api.model
    def _do_verify_hcaptcha_token(self, qcontext):
        ip_addr = request.httprequest.remote_addr
        resp_token = qcontext.get("hcaptcha_resp_token")
        recaptcha_result = self._verify_hcaptcha_token(ip_addr, resp_token)
        if recaptcha_result in ["is_human", "no_secret"]:
            return
        if recaptcha_result == "wrong_secret":
            raise ValidationError(_("The hCaptcha private key is invalid."))
        elif recaptcha_result == "wrong_token":
            raise ValidationError(_("The hCaptcha token is invalid."))
        elif recaptcha_result == "timeout":
            raise UserError(_("Your request has timed out, please retry."))
        elif recaptcha_result == "bad_request":
            raise UserError(_("The request is invalid or malformed."))

    @http.route()
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if "error" not in qcontext and request.httprequest.method == "POST":
            try:
                self._do_verify_hcaptcha_token(qcontext)
            except Exception as e:
                request.params.update({"error": e.args[0]})  # 更新qcontext
        return super(AuthSignup, self).web_auth_reset_password(*args, **kw)

    @http.route()
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if "error" not in qcontext and request.httprequest.method == "POST":
            try:
                self._do_verify_hcaptcha_token(qcontext)
            except Exception as e:
                request.params.update({"error": e.args[0]})  # 更新qcontext
        return super(AuthSignup, self).web_auth_signup(*args, **kw)
