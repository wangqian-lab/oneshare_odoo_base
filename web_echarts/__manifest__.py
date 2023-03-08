# -*- coding: utf-8 -*-
{
    "name": "web_echarts",
    "summary": """
        echarts插件""",
    "description": """
        echarts插件
    """,
    "author": "上海文享数据科技有限公司",
    "website": "http://www.oneshare.com.cn",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Hidden/Tools",
    "version": "14.0.0.1",
    # any module necessary for this one to work correctly
    "depends": ["web"],
    # always loaded
    "data": [
        "views/web_widget_echart.xml",
    ],
}
