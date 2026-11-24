# -*- coding: utf-8 -*-
{
    'name': "POS Partner Ref",

    'summary': "Inherit POS for Partner Ref",

    'description': """
Add Partner Ref List to POS
    """,

    'author': "SMEi",
    'website': "https://www.smeintellect.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Point of Sale',
    'version': '0.1',
    'license': 'LGPL-3',
    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale'],

    # always loaded
    # 'data': [
    #     'views/pos_order_views.xml',
    # ],

    # 'assets':{
    #     'point_of_sale._assets_pos':[
    #         "cll_pos_partneref/static/src/app/**/*",
    #     ],
    # },
    'application' : True,
    'license': 'LGPL-3'
}
