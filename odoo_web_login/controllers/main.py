# -*- encoding: utf-8 -*-
##############################################################################
#
#    Samples module for Odoo Web Login Screen
#    Copyright (C) 2017- XUBI.ME (http://www.xubi.me)
#    @author binhnguyenxuan (https://www.linkedin.com/in/binhnguyenxuan)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#    
#
##############################################################################

import ast
from odoo.addons.web.controllers.main import Home
from odoo.addons.web.controllers.main import SIGN_UP_REQUEST_PARAMS as Prev_SIGN_UP_REQUEST_PARAMS
import pytz
import datetime
import logging
from distutils.util import strtobool

import odoo
import odoo.modules.registry
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

New_SIGN_UP_REQUEST_PARAMS = {'disable_footer', 'disable_database_manager', 'background_src'}
New_SIGN_UP_REQUEST_PARAMS.update(Prev_SIGN_UP_REQUEST_PARAMS)

odoo.addons.web.controllers.main.SIGN_UP_REQUEST_PARAMS = New_SIGN_UP_REQUEST_PARAMS


# ----------------------------------------------------------
# Odoo Web web Controllers
# ----------------------------------------------------------
class LoginHome(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        param_obj = request.env['ir.config_parameter'].sudo()
        request.params['disable_footer'] = param_obj.get_param('login_form_disable_footer') or False
        request.params['disable_database_manager'] = param_obj.get_param('login_form_disable_database_manager') or False

        change_background = param_obj.get_param('login_form_change_background_by_hour') or False
        if change_background:
            config_login_timezone = param_obj.get_param('login_form_change_background_timezone')
            tz = config_login_timezone and pytz.timezone(config_login_timezone) or pytz.utc
            current_hour = datetime.datetime.now(tz=tz).hour or 10

            if (0 <= current_hour < 3) or (18 <= current_hour < 24):  # Night
                request.params['background_src'] = param_obj.get_param('login_form_background_night') or ''
            elif 3 <= current_hour < 7:  # Dawn
                request.params['background_src'] = param_obj.get_param('login_form_background_dawn') or ''
            elif 7 <= current_hour < 16:  # Day
                request.params['background_src'] = param_obj.get_param('login_form_background_day') or ''
            else:  # Dusk
                request.params['background_src'] = param_obj.get_param('login_form_background_dusk') or ''
        else:
            request.params['background_src'] = param_obj.get_param('login_form_background_default') or ''
        return super(LoginHome, self).web_login(redirect, **kw)
