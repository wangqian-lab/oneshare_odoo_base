# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import pathlib

from odoo.addons.onesphere_certification_authority.tests.common import (
    TestOneshareCACommon,
)
from odoo.tests import new_test_user, tagged, Form
from odoo.addons.oneshare_utils.constants import (
    ONESHARE_CRYPT_NONCE,
    ONESHARE_CRYPT_ASSOCIATED_DATA,
)
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import json
import base64

cwd_path = Path(__file__)


@tagged("-standard", "ca")
class TestOneshareResConfig(TestOneshareCACommon):
    def setUp(self):
        super(TestOneshareResConfig, self).setUp()
        self._obj = self.env["res.config.settings"]

    def test_generate_secret_key(self):
        key = self._obj.generate_secret_key()
        key = base64.b64decode(key.encode("utf-8"))
        f = ChaCha20Poly1305(key)
        f.generate_key()
        d = {"test": 111}
        data = json.dumps(d)
        token = f.encrypt(
            ONESHARE_CRYPT_NONCE, data.encode("utf-8"), ONESHARE_CRYPT_ASSOCIATED_DATA
        )
        f = ChaCha20Poly1305(key)
        s = f.decrypt(ONESHARE_CRYPT_NONCE, token, ONESHARE_CRYPT_ASSOCIATED_DATA)
        ss = json.loads(s.decode("utf-8"))
        self.assertEqual(ss.get("test"), d.get("test"))
