# -*- coding: utf-8 -*-
{
    'name': "SMEi Transaction Currency Rate",

    'summary': """
        SMEi Currency rate""",

    'description': """
        SMEi Currency rate
    """,

    'author': "SME Intellect Co. Ltd",
    'website': "https://www.smeintellect.com/",
    'category': 'Accounting Management',
    'version': '0.1',
    'depends': ['account','sale','purchase','stock'],
    'data': [
        'views/sale_order_vew.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/purchase_order_view.xml',
        'views/hr_expense_view.xml',
    ],
    'license': 'LGPL-3',

}
