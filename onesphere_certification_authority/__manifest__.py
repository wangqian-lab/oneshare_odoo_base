# -*- coding: utf-8 -*-
{
    'name': "onesphere_certification_authority",

    'summary': """
        认证中心""",

    'description': """
        认证中心
    """,

    'author': "上海文享数据科技有限公司",
    'website': "http://www.oneshare.com.cn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Administration',
    'version': '14.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/cryptography_key_sequence.xml',
        'views/res_config_settings_views.xml',
        'views/certification_views.xml',
        'wizard/oneshare_issued_certification_view.xml',
        'views/base_views.xml',
    ]
}
