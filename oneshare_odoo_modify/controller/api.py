# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID, api
from odoo.http import request, Response

import http as httplib
import json


class BaseApi(http.Controller):
    @http.route('/api/v1/logo', type='http', auth='none', cors='*', csrf=False)
    def _get_default_logo(self):
        env = api.Environment(request.cr, SUPERUSER_ID, request.context)
        company = env['res.company'].search([])
        logo = company[0].logo
        if not logo:
            body = json.dumps({'msg': 'Logo not found'})
            return Response(body, headers=[('Content-Type', 'application/json'), ('Content-Length', len(body))],
                            status=404)
        ret = {
            "logo": u'data:{0};base64,{1}'.format('image/png', company[0].logo) if company[0].logo else ""
        }
        body = json.dumps(ret)
        return Response(body, headers=[('Content-Type', 'application/json'), ('Content-Length', len(body))], status=200)

    @http.api_route('/api/v1/healthz', type='http', auth='none', cors='*', csrf=False)
    def _healthz(self, *args, **kwargs):
        return Response(status=httplib.HTTPStatus.NO_CONTENT)
