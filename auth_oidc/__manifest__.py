{
    "name": "Authentication OpenID Connect",
    "version": "14.0.1.0.2",
    "license": "AGPL-3",
    "author": (
        "ICTSTUDIO, André Schenkels, "
        "ACSONE SA/NV, "
        "Odoo Community Association (OCA)"
    ),
    "website": "https://www.oneshare.com.cn",
    "summary": "Allow users to login through OpenID Connect Provider",
    "external_dependencies": {"python": ["python-jose"]},
    "depends": ["auth_oauth"],
    "data": [
        "data/base_groups.xml",
        "views/auth_oauth_provider.xml",
        'views/res_config_settings_views.xml'
    ],
    "demo": [
        "demo/local_keycloak.xml"
    ],
    'post_init_hook': '_auto_load_oneshare_oidc_settings',
}
