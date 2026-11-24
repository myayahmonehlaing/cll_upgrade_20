# -*- coding: utf-8 -*-
{
    'name': "CLL Provider Fees ",

    'summary': "CLL Provider Fees  ",

    'description': """
       Sales
    """,

    'author': "SME Intellect Co.,Ltd",
    'website': "https://www.smeintellect.com",

    'category': 'sale',
    'version': '0.1',

    'depends': ['sale','account'],

    # always loaded
    'data': [
        # 'security/security.xml',
        'security/ir.access.csv',
        'views/provider_fee_policy_view.xml',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',

    ],
    "license": "AGPL-3",
    "applications": True,
    "installable": True,
    "auto_install": False,
}
