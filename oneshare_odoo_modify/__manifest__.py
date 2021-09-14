# -*- coding: utf-8 -*-
{
    'name': "oneshare_odoo_modify",

    'summary': """
        上海文享信息科技有限公司odoo官方基础扩展模块""",

    'description': """
        1. 增加TIMESCALEDB数据库支持
        2. 增加了新的模型hyperModel,支持时序数据
        3. 增加了新的http route type: apijson, 并提供bearer token的认证支持
    """,

    'author': "Oneshare",
    'website': "http://www.oneshare.com.cn",


    'category': 'Base',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['web','base', 'resource'],
    "data": ["templates/assets.xml"],
    'auto_install': True,
    'post_init_hook': '_auto_load_onesphere_default_partner_settings',
}
