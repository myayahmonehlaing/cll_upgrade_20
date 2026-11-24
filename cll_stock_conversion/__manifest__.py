# -*- coding: utf-8 -*-
{
    'name': "CLL Product Conversion ",

    'summary': "CLL Product Conversion  ",

    'description': """
       Inventory Management
    """,

    'author': "SME Intellect",
    'website': "https://www.smeintellect.com",

    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock','mrp'],

    # always loaded
    'data': [

        'security/ir.access.csv',
        'wizard/stock_picking_convertion_views.xml',
        'views/product_views.xml',
        'views/stock_picking_views.xml',


    ],
    "license": "AGPL-3",
    "applications": True,
    "installable": True,
    "auto_install": False,
}
