# -*- coding: utf-8 -*-
{
    "name": "auth_signup_hcaptcha",
    "summary": """
        Hcaptcha 防机器人集成""",
    "description": """
        Hcaptcha 防机器人集成
    """,
    "author": "上海文享数据科技有限公司",
    "website": "http://www.oneshare.com.cn",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Hidden",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["auth_signup", "web"],
    # always loaded
    "data": [
        # 'security/ir.model.access.csv',
        "views/res_config_settings_view.xml",
        "views/signup_templates.xml",
    ],
}
