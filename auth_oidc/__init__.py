from . import controllers
from . import models
from distutils.util import strtobool
import os
from odoo import api, SUPERUSER_ID

ENV_ENABLE_SSO = strtobool(os.getenv("ENV_ENABLE_SSO", "False"))


def _auto_load_oneshare_oidc_settings(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ResConfig = env["res.config.settings"]
    default_values = ResConfig.default_get(list(ResConfig.fields_get()))
    if ENV_ENABLE_SSO:
        default_values.update({"sso_enable": True})
    ResConfig.create(default_values).execute()
    cr.commit()
