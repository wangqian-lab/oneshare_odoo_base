# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
import os

ENV_DEFAULT_LANGUAGE = os.getenv("ENV_DEFAULT_LANGUAGE", "zh_CN")


@api.model
def _lang_get(self):
    return self.env["res.lang"].get_installed()


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_auth_signup_hcaptcha = fields.Boolean(
        "hCAPTCHA: Easy on Humans, Hard on Bots"
    )

    hcaptcha_public_key = fields.Char(
        "Site Key", config_parameter="hcaptcha_public_key", groups="base.group_system"
    )
    hcaptcha_private_key = fields.Char(
        "Secret Key",
        config_parameter="hcaptcha_private_key",
        groups="base.group_system",
    )
    hcaptcha_lang = fields.Selection(
        _lang_get,
        string="Hcaptcha Load Language",
        config_parameter="hcaptcha_lang",
        default=ENV_DEFAULT_LANGUAGE,
    )
