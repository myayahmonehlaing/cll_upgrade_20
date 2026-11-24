# -*- coding: utf-8 -*-
{
    "name": "CLL Sales ",
    "summary": "CLL Sales  ",
    "description": """
       Sales
    """,
    "author": "SME Intellect",
    "website": "https://www.smeintellect.com",
    "category": "sale",
    "version": "0.1",
    # any module necessary for this one to work correctly
    "depends": ["sale", "account", 'sale_purchase','product_expiry'],
    # always loaded
    "data": [
        "views/res_partner_group_views.xml",
        "views/sale_order_view.xml",
        'views/product_views.xml',
        "views/res_partner_views.xml",
        "views/account_move_views.xml",
        # 'security/res_partner_security.xml',
        # 'security/product_security.xml',
        "security/ir.access.csv",
    ],
    "license": "AGPL-3",
    "applications": True,
    "installable": True,
    "auto_install": False,
}
