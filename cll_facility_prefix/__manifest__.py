# -*- coding: utf-8 -*-
{
    'name': "CLL Custom Sequence ",

    'summary': "CLL Custom  ",

    'description': """
        Customization of Sequence by facility prefix 
    """,

    'author': "SME Intellect",
    'website': "https://www.smeintellect.com",

    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sale','stock','purchase','account_cashbook',
                'sale_purchase','stock_account','hr_expense','approvals','point_of_sale'],

    # always loaded
    'data': [

        'views/res_config_settings_views.xml',
        'views/res_facility_views.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'views/purchase_order_view.xml',
        'views/stock_inventory_adjustment_name_view.xml',
        'views/stock_warehouse_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/hr_expense_sheet_view.xml',
        'views/approval_request_view.xml',
        'views/account_cashbook_view.xml',
        'views/account_analytic_plan_views.xml',
        'views/product_product_view.xml',
        'views/pos_config_view.xml',
        'views/pos_order_views.xml',
        'security/ir.access.csv',

    ],
    "license": "AGPL-3",
    "applications": True,
    "installable": True,
    "auto_install": False,
}
