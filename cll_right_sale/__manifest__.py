# -*- coding: utf-8 -*-
{
    'name': "Right Sale Customization",

    'summary': "Customization of sale process",

    'description': """
Sale process customization especially for the Rightlab Health Care
    """,

    'author': "SMEi, DUYK",
    'website': "https://www.smeintellect.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'sale_stock', 'cll_sale'],

    # always loaded
    'data': [
        'security/security.xml',
        'data/ir_config_parameter.xml',
        'views/res_config_settings_views.xml',
        'views/sale_center_views.xml',
        'views/sale_order_views.xml',
        'security/ir.access.csv',

    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}

