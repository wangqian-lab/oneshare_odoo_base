# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request

import jwt
import datetime

s = jwt.encode(
    {'key': 'value',
     'aud': ['admin', 'test']},
    'secret',
    algorithm='HS256'
)
print(s)

# ns = jwt.decode(s, 'secret', algorithm='HS256')
ns = jwt.decode(s, audience='test', options={'verify_signature': False})
print(ns)
print(jwt.get_unverified_header(s))
