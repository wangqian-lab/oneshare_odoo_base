# -*- coding: utf-8 -*-
{
    "name": "oneshare_website_slide_iframe",
    "summary": """
        支持直接嵌入iframe""",
    "description": """
        支持直接嵌入iframe
    """,
    "author": "上海文享数据科技有限公司",
    "website": "http://www.oneshare.com.cn",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Website/eLearning",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["website_slides"],
    # always loaded
    "data": [
        "views/assets.xml",
        "views/slide_slide_views.xml",
        "views/website_slides_templates_lesson.xml",
        "views/website_slides_templates_lesson_fullscreen.xml",
    ],
}
