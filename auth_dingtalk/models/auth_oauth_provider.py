from odoo import fields, models


class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    client_secret = fields.Char(
        help="Used in OpenID Connect authorization code flow for confidential clients.",
    )
