# -*- encoding: utf-8 -*-

import os
import base64

ONESHARE_DEFAULT_LIMIT = int(os.getenv('ENV_ONESHARE_SQL_REC_LIMT', '15'))
ENV_ONESHARE_CRYPT_NONCE = os.getenv('ENV_ONESHARE_CRYPT_NONCE', 'oneshare')
ENV_ONESHARE_CRYPT_ASSOCIATED_DATA = os.getenv('ENV_ONESHARE_CRYPT_ASSOCIATED_DATA',
                                               'Authenticated By Oneshare Co. Ltd.')

ONESHARE_CRYPT_NONCE = base64.b64encode(ENV_ONESHARE_CRYPT_NONCE.encode('utf-8'))
ONESHARE_CRYPT_ASSOCIATED_DATA = base64.b64encode(ENV_ONESHARE_CRYPT_ASSOCIATED_DATA.encode('utf-8'))


ENV_OSS_BUCKET = os.getenv('ENV_OSS_BUCKET', 'oneshare')
ENV_OSS_ENDPOINT = os.getenv('ENV_OSS_ENDPOINT', '127.0.0.1:9000')
ENV_OSS_ACCESS_KEY = os.getenv('ENV_OSS_ACCESS_KEY', 'minio')
ENV_OSS_SECRET_KEY = os.getenv('ENV_OSS_SECRET_KEY', 'minio123')

# SPC相关
ONESHARE_DEFAULT_SPC_MIN_LIMIT = int(os.getenv('ONESHARE_DEFAULT_SPC_MIN_LIMIT', '50'))
ONESHARE_DEFAULT_SPC_MAX_LIMIT = int(os.getenv('ONESHARE_DEFAULT_SPC_MAX_LIMIT', '1000'))

