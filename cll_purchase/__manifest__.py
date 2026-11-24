# -*- coding: utf-8 -*-
{
    'name': "CLL Purchase ",

    'summary': "CLL Purchase  ",

    'description': """
       Purchase
    """,

    'author': "SME Intellect",
    'website': "https://www.smeintellect.com",

    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase','cll_account'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'views/purchase_order_view.xml',
        'wizard/purchase_apporval_request_view.xml',
        'views/account_move_view.xml',
        'views/stock_picking_view.xml',
    ],
    "license": "AGPL-3",
    "applications": True,
    "installable": True,
    "auto_install": False,
}
