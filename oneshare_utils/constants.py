# -*- encoding: utf-8 -*-

import os
import base64

ONESHARE_DEFAULT_LIMIT = int(os.getenv('ENV_ONESHARE_SQL_REC_LIMT', '15'))
ENV_ONESHARE_CRYPT_NONCE = os.getenv('ENV_ONESHARE_CRYPT_NONCE', 'oneshare')
ENV_ONESHARE_CRYPT_ASSOCIATED_DATA = os.getenv('ENV_ONESHARE_CRYPT_ASSOCIATED_DATA',
                                               'Authenticated By Oneshare Co. Ltd.')

ONESHARE_CRYPT_NONCE = base64.b64encode(ENV_ONESHARE_CRYPT_NONCE.encode('utf-8'))
ONESHARE_CRYPT_ASSOCIATED_DATA = base64.b64encode(ENV_ONESHARE_CRYPT_ASSOCIATED_DATA.encode('utf-8'))
