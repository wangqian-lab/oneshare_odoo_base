# -*- coding: utf-8 -*-

from . import http
from . import db
from . import model
from . import models
from . import controller
from odoo import tools
from odoo.models import SUPERUSER_ID, api
import os

ENV_DEFAULT_LANGUAGE = os.getenv("ENV_DEFAULT_LANGUAGE", "zh_CN")
ENV_DEFAULT_TIMEZONE = os.getenv("ENV_DEFAULT_TIMEZONE", "Asia/Shanghai")


def _default_timezone_lang_cn(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    res_partner_model = env["res.partner"]
    all_users = res_partner_model.search([(1, "=", 1)])
    val = {
        "tz": ENV_DEFAULT_TIMEZONE,
        "lang": ENV_DEFAULT_LANGUAGE,
        "country_id": env.ref("base.cn").id,
    }
    all_users.write(val)
    cr.commit()


def _auto_load_onesphere_default_partner_settings(cr, registry):
    tools.load_language(cr, ENV_DEFAULT_LANGUAGE)
    _default_timezone_lang_cn(cr)
