# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import MissingError


class OneshareModal(models.TransientModel):
    _name = "oneshare.modal"
    _description = "Oneshare Modal - Wizard Model"

    @api.model
    def _default_res_model_id(self):
        res_model_name = self.env.context.get("active_model")
        return self.env["ir.model"].search([("model", "=", res_model_name)])

    @api.model
    def _default_res_record_id(self):
        return self.env.context.get("active_record_id", 0)

    @api.model
    def _default_res_record(self):
        res_model_name = self._default_res_model_id().model
        try:
            res_model_model = self.env[res_model_name]
        except KeyError:
            return None

        return res_model_model.browse(self._default_res_record_id())

    @api.model
    def _default_res_field_id(self):
        res_model_id = self._default_res_model_id()
        res_field_name = self.env.context.get("active_field")
        return self.env["ir.model.fields"].search(
            [
                ("model_id", "=", res_model_id.id),
                ("name", "=", res_field_name),
            ]
        )

    @api.model
    def _default_image(self):
        res_record = self._default_res_record()
        res_field_name = self._default_res_field_id().name

        try:
            return getattr(res_record, res_field_name, None)
        except (TypeError, MissingError):
            return None

    res_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Source Model",
        required=True,
        default=lambda self: self._default_res_model_id(),
    )
    res_record_id = fields.Integer(
        string="Source Record ID",
        required=True,
        default=lambda self: self._default_res_record_id(),
    )
    res_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Source Field",
        required=True,
        default=lambda self: self._default_res_field_id(),
    )
    image = fields.Binary(
        string="Image",
        required=True,
        default=lambda self: self._default_image(),
    )

    def action_save(self):
        self.ensure_one()
        return {"type": "ir.actions.act_window_close"}

    def get_image_editor_action(self):
        return self.env.ref("web_image_editor.oneshare_modal_view_form").id
