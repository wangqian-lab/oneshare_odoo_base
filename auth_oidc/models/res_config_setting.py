# -*- coding: utf-8 -*-
# License AGPL-3
from odoo import api, fields, models, _
import os

DefaultProviderName = "KeyCloak"


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sso_provider = fields.Char(default=DefaultProviderName,
                               string='SSO Provider',
                               config_parameter='sso.provider')

    sso_enable = fields.Boolean(default=False,
                                string='SSO Enable',
                                config_parameter='sso.enabled')
