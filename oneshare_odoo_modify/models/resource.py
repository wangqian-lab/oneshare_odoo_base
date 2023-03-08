# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import os

ENV_DEFAULT_TIMEZONE = os.getenv("ENV_DEFAULT_TIMEZONE", "Asia/Shanghai")


class ResourceResource(models.Model):
    _inherit = "resource.resource"

    resource_type = fields.Selection(
        selection_add=[("area", _("Area"))], ondelete={"area": "set default"}
    )
    tz = fields.Selection(default=ENV_DEFAULT_TIMEZONE)


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    tz = fields.Selection(default=ENV_DEFAULT_TIMEZONE)
