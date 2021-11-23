# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, formatLang
from odoo.addons.oneshare_utils.constants import ONESHARE_CRYPT_NONCE, ONESHARE_CRYPT_ASSOCIATED_DATA
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import ec


class OneshareIssuedCertWizard(models.TransientModel):
    _name = 'onesahre.issue.cert.wizard'
    _description = 'Issue Cert Wizard'

    crypt_key_id = fields.Many2one('oneshare.cryptography.key', 'Key', required=True)
    revision = fields.Char(string='Rev', related='crypt_key_id.revision')
    content = fields.Text('Raw Content', required=True)

    def do_action(self):
        self.ensure_one()
        if not self.content or not self.crypt_key_id:
            return
        secret_key = self.crypt_key_id.secret_key
        key = base64.b64decode(secret_key.encode('utf-8'))
        f = ChaCha20Poly1305(key)
        data = self.content
        token = f.encrypt(ONESHARE_CRYPT_NONCE, data.encode('utf-8'), ONESHARE_CRYPT_ASSOCIATED_DATA)
        b_encrypted_license = token[:-16]
        base64_token = base64.b64encode(token)
        hasher = hashes.Hash(hashes.SHA256())
        hasher.update(b_encrypted_license)
        digest = hasher.finalize()  # 摘要
        private_key_content = self.crypt_key_id.private_key.encode('utf-8')
        private_key = load_pem_private_key(private_key_content, password=None)
        signature_content = private_key.sign(digest, ec.ECDSA(hashes.SHA256()))  # 签名
        val = {
            'crypt_key_id': self.crypt_key_id.id,
            'content': self.content,
            'crypt_content': base64_token.decode('utf-8'),
            'digest': base64.b64encode(digest).decode('utf-8'),
            'signature': base64.b64encode(signature_content).decode('utf-8'),
        }
        certification_obj = self.env['oneshare.certification']
        ret = certification_obj.create(val)
        if not ret:
            raise UserError('Create Issued Cert Fail')
        form = self.env.ref('onesphere_certification_authority.oneshare_issued_cert_view_form',
                            raise_if_not_found=False)
        return {
            'name': _('Issued Certification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': ret.id,
            'res_model': 'oneshare.certification',
            'views': [(form.id, 'form')],
            'view_id': form.id,
            'context': self.env.context,
        }
