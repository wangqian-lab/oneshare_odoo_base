# -*- coding: utf-8 -*-
# License AGPL-3
from odoo import api, fields, models, _
import os
import base64
from cryptography.hazmat.primitives.asymmetric import ec, dsa, rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

Algorithm = [("RSA", "RSA"), ("DSA", "DSA"), ("ECDSA", "ECDSA")]

AlgorithmMap = {"RSA": rsa, "DSA": dsa, "ECDSA": ec}


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ca_algorithm = fields.Selection(
        Algorithm, default="ECDSA", string="认证加密算法", config_parameter="ca.algorithm"
    )
    ca_private_key = fields.Char(string="认证私钥", config_parameter="ca.private_key")
    ca_public_key = fields.Char(string="认证公钥", config_parameter="ca.public_key")

    ca_secret_key = fields.Char(string="对称加密秘钥", config_parameter="ca.secret_key")

    def set_values(self):
        return super(ResConfigSettings, self).set_values()

    @staticmethod
    def generate_secret_key() -> str:
        d = ChaCha20Poly1305.generate_key()
        key = base64.b64encode(d).decode("utf-8")
        return key

    def generate_certification_bundle(self):
        if self.ca_algorithm == "ECDSA":
            private_key = ec.generate_private_key(ec.SECP521R1())
            public_key = private_key.public_key()
        self.ca_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        self.ca_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.ca_secret_key = self.generate_secret_key()
        self.set_values()
        vals = {
            "private_key": self.ca_private_key,
            "public_key": self.ca_public_key,
            "secret_key": self.ca_secret_key,
        }
        ret = self.env["oneshare.cryptography.key"].sudo().create(vals)
        form = self.env.ref(
            "onesphere_certification_authority.oneshare_crypt_key_view_form",
            raise_if_not_found=False,
        )
        return {
            "name": _("Crypt Key"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_id": ret.id,
            "res_model": "oneshare.cryptography.key",
            "views": [(form.id, "form")],
            "view_id": form.id,
            "context": self.env.context,
        }
