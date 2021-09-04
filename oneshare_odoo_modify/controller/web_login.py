# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID, api
from odoo.http import request, Response
from http import HTTPStatus
import odoo
import json
from odoo.addons.web.controllers.main import ensure_db


class WebLogin(http.Controller):
    @http.api_route('/api/v1/login', type='apijson', auth='none', cors='*', csrf=False)
    def _login(self, **kwargs):
        params = kwargs
        login = params.get('login')
        password = params.get('password')
        if not login or not password:
            return Response(json.dumps({'msg': 'Login Parameter Is Missing'}),
                            headers={'content-type': 'application/json'},
                            status=HTTPStatus.BAD_REQUEST)
        ensure_db()
        if not request.session.db:
            return Response(json.dumps({'msg': 'Database not found'}), headers={'content-type': 'application/json'},
                            status=HTTPStatus.BAD_REQUEST)
        db = request.session.db
        # res_users = odoo.registry(db)['res.users']
        uid = request.session.authenticate(db, login, password)
        if not uid:
            return Response(json.dumps({'msg': 'User Auth Fail'}), headers={'content-type': 'application/json'},
                            status=HTTPStatus.BAD_REQUEST)

        user_id = request.env['res.users'].sudo().browse(uid)
        if not user_id:
            return Response(json.dumps({'msg': 'User Access Deny'}), headers={'content-type': 'application/json'},
                            status=HTTPStatus.BAD_REQUEST)
        ret = {
            'id': user_id.id,
            'database': db,
            'name': user_id.name,
            'login': user_id.login,
            'status': 'active' if user_id.active else 'inactive',
            'token': user_id._compute_session_token(request.session.sid),
            'session_id': request.session.sid,
            'image_small': u'data:{0};base64,{1}'.format('image/png',
                                                         user_id.image_128) if user_id.image_128 else ""
        }
        request.session.modified = False
        return Response(json.dumps(ret), headers={'content-type': 'application/json'},
                        status=HTTPStatus.OK)
