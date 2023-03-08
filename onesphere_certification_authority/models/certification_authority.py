# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class OneshareCryptographyKey(models.Model):
    _name = "oneshare.cryptography.key"
    _description = "秘钥"
    _rec_name = "revision"
    _order = "revision desc"

    _check_company_auto = True

    @api.depends("certification_ids")
    def _compute_certification_count(self):
        for r in self:
            r.certification_count = 0
            if not r.certification_ids:
                continue
            r.certification_count = len(r.certification_ids)

    revision = fields.Char(
        string="Rev",
        required=True,
        copy=False,
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "onesphere_certification_authority.cryptography_key_revision"
        ),
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    private_key = fields.Text("Private Key", required=True, copy=False, default="")
    public_key = fields.Text("Public Key", required=True, copy=False, default="")
    secret_key = fields.Text("Secret Key", required=True, copy=False, default="")
    certification_ids = fields.One2many(
        "oneshare.certification", "crypt_key_id", string="Certifications"
    )
    certification_count = fields.Integer(
        "Certification Count", compute=_compute_certification_count
    )
    active = fields.Boolean("Active", default=True)

    def action_open_related_certification_tree_view(self):
        self.ensure_one()
        if not self.certification_ids:
            return
        return {
            "name": _("Issued Certification"),
            "type": "ir.actions.act_window",
            "res_model": "oneshare.certification",
            "views": [
                [
                    self.env.ref(
                        "onesphere_certification_authority.oneshare_issued_cert_view_tree"
                    ).id,
                    "tree",
                ]
            ],
            "domain": [("id", "in", self.certification_ids.ids)],
            "target": "main",
        }

    @api.model
    def create(self, vals):
        if not vals.get("revision", None):
            vals.update(
                {
                    "revision": self.env["ir.sequence"].next_by_code(
                        "cryptography_key_revision"
                    )
                }
            )
        self.search([]).write({"active": False})  # 所有记录inactive
        record = super().create(vals)
        return record

    def issued_certification(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "onesphere_certification_authority.oneshare_issue_cert_wizard_action"
        )
        ctx = dict(self.env.context)
        ctx.pop("active_id", None)
        ctx["default_crypt_key_id"] = self.id
        action["context"] = ctx
        return action

    class OneshareIssuedCertification(models.Model):
        _name = "oneshare.certification"
        _description = "签发证书"
        _rec_name = "revision"
        _order = "id"
        _check_company_auto = True

        crypt_key_id = fields.Many2one("oneshare.cryptography.key", "Key")
        revision = fields.Char(
            string="Rev", related="crypt_key_id.revision", store=True
        )
        secret_key = fields.Text(
            "Secret Key", related="crypt_key_id.secret_key", store=True
        )
        content = fields.Text("Raw Content")
        crypt_content = fields.Text(string="Crypt Content", help="Crypt Content")
        digest = fields.Text(string="Digest")
        signature = fields.Text("Signature")
        company_id = fields.Many2one(
            "res.company",
            string="Company",
            required=True,
            default=lambda self: self.env.company,
        )
