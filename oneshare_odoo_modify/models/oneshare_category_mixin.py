# -*- coding: utf-8 -*-

from odoo import models, fields, api
from random import randint


class OneshareCategoryMixin(models.AbstractModel):
    _name = "oneshare.category.mixin"
    _description = "Category Mixin"

    @staticmethod
    def _get_default_color():
        return randint(1, 11)

    name = fields.Char(string="Tag Name", required=True)
    color = fields.Integer(string="Color Index", default=_get_default_color)
