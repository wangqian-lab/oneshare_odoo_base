# -*- coding: utf-8 -*-
{
    'name': "auth_dingtalk",

    'summary': """
        钉钉登陆""",

    'description': """
        钉钉登陆
    """,

    'author': "Oneshare",
    'website': "http://www.oneshare.com.cn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Base',
    'version': '14.0.1.1',

    # any module necessary for this one to work correctly
    'depends': ['auth_oidc'],

    # always loaded
    'data': [
        'data/dingtalk.xml'
    ],
}
