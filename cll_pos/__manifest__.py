# -*- coding: utf-8 -*-
{
    'name': "CLL POS ",

    'summary': "CLL POS  ",

    'description': """
        Customization of POS Purchase Order 
    """,

    'author': "SME Intellect",
    'website': "https://www.smeintellect.com",

    'category': 'Point Of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'sale_purchase', 'cll_sale'],

    # always loaded
    'data': [
        'security/ir.access.csv',
        'data/picking_cron.xml',
        'views/pos_order_views.xml',
        'views/product_view.xml',
        # 'views/res_config_settings_views.xml',
        'views/res_users_view.xml',
        'views/stock_picking_view.xml',
        # 'security/security.xml',
        'wizard/pos_order_layout_views.xml',
        'report/pos_oder_templates.xml',
        'report/pos_order_report.xml',
    ],
    # 'assets': {
    #     'point_of_sale._assets_pos': [
    #         'cll_pos/static/src/**/*',
    #     ],
    #     'pos_self_order.assets': [
    #         'cll_pos/static/src/css/*',
    #         ]
    #     ,
    # },
    "license": "AGPL-3",
    "applications": True,
    "installable": True,
    "auto_install": False,
}
