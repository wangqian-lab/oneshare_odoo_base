# -*- coding: utf-8 -*-
# License AGPL-3
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wxapp_app_id = fields.Char(
        string='微信小程序APPID',
        config_parameter='wxapp.app_id')
    wxapp_app_secret = fields.Char(
        string='微信小程序APP Secret',
        config_parameter='wxapp.app_secret')
