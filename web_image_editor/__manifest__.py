# -*- coding: utf-8 -*-
{
    'name': "web_image_editor",

    'summary': """
        图片编辑控件""",

    'description': """
        图片编辑控件
    """,

    'author': "上海文享数据科技有限公司",
    'website': "http://www.oneshare.com.cn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '14.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'wizards/oneshare_modal.xml',
    ],
    'qweb': [
        "static/src/xml/template.xml",
    ],
}
