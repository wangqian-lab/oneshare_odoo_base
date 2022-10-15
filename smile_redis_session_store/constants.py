# -*- coding: utf-8 -*-

import os
from distutils.util import strtobool

from odoo.addons.oneshare_odoo_modify.http import SESSION_TIMEOUT as ODOO_SESSION_TIMEOUT

from odoo import tools

SESSION_TIMEOUT = ODOO_SESSION_TIMEOUT

redis_hosts: str = tools.config.get('redis_host', None) or os.getenv('ENV_REDIS_HOST', 'localhost')
startup_nodes = redis_hosts.split(',')

redis_ports = int(tools.config.get('redis_port') or os.getenv('ENV_REDIS_PORT', '6379'))
redis_db = int(tools.config.get('redis_dbindex') or os.getenv('ENV_SESSION_REDIS_DB', '1'))
redis_password = tools.config.get('redis_pass') or os.getenv('ENV_REDIS_PASSWORD', None)


def is_redis_session_store_activated():
    return tools.config.get('enable_redis') or strtobool(os.getenv('ENV_SESSION_REDIS_ENABLE', 'False'))
