# -*- coding: utf-8 -*-
# ----------------------------------------------------------
# ir_http modular http routing
# ----------------------------------------------------------
import base64
import hashlib
import logging
import mimetypes
import os
import re
import sys
import traceback

import werkzeug
import werkzeug.exceptions
import werkzeug.routing
import werkzeug.urls
import werkzeug.utils

from odoo.models import _
from odoo import api, http, models, tools, SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError, MissingError
from odoo.http import request, content_disposition
from odoo.tools import consteq, pycompat
from odoo.tools.mimetypes import guess_mimetype
from odoo.modules.module import get_resource_path, get_module_path

from odoo.http import ALLOWED_DEBUG_MODES
from odoo.tools.misc import str2bool

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_bear_token(cls):
        if request.session.uid:
            request.uid = request.session.uid
            return
        httprequest = request.httprequest
        if "authorization" not in httprequest.headers:  # token 不存在
            raise AccessDenied(_('API Authorization Error, Authorization Part Not In HTTP Headers'))
        token_part = httprequest.headers.get("authorization", "").split(' ')
        if len(token_part) < 2:
            raise AccessDenied('API Authorization Error, Authorization Part Is Not Right: {}'.format(token_part))
        if token_part[0] != 'Bearer':
            raise AccessDenied(
                'API Authorization Error, Authorization Part Bearer Key Is Not Present: {}'.format(token_part))
        user = request.env['res.users'].sudo().search([('api_token', '=', token_part[1])])
        if not user:
            raise AccessDenied(
                'API Authorization Error, API Token Is Not Found: {}'.format(token_part))
        request.uid = user.id

    @classmethod
    def _authenticate(cls, endpoint):
        # if endpoint.routing["type"] == 'apijson' and endpoint.routing["auth"] == 'user':
        #     endpoint.routing.update({
        #         'auth': 'bear_token'
        #     })
        return super(IrHttp, cls)._authenticate(endpoint)
