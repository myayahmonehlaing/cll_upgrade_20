# -*- coding: utf-8 -*-
{
    'name': "CLL Stock ",

    'summary': "CLL Stock  ",

    'description': """
       Stock
    """,

    'author': "SME Intellect",
    'website': "https://www.smeintellect.com",

    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock','sale_stock', 'product_expiry','stock_account',
                'sale','stock_analytic'],

    # always loaded
    'data': [
        'security/ir.access.csv',
        'security/product_security.xml',
        'security/res_partner_security.xml',
        'views/stock_quant_views.xml',
        'views/stock_move_views.xml',
        'views/report_template.xml',
        'report/stock_report_views.xml',
        'views/stock_picking_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'cll_stock/static/src/**/*',]
    },
    "license": "AGPL-3",
    "applications": True,
    "installable": True,
    "auto_install": False,
}
