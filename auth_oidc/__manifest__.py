{
    "name": "Authentication OpenID Connect",
    "version": "13.0.1.0.1",
    "license": "AGPL-3",
    "author": (
        "ICTSTUDIO, André Schenkels, "
        "ACSONE SA/NV, "
        "Odoo Community Association (OCA)"
    ),
    "maintainers": ["sbidoul"],
    "website": "https://github.com/OCA/server-auth",
    "summary": "Allow users to login through OpenID Connect Provider",
    "external_dependencies": {"python": ["python-jose"]},
    "depends": ["auth_oauth"],
    "data": ["views/auth_oauth_provider.xml"],
    "demo": ["demo/local_keycloak.xml"],
}
