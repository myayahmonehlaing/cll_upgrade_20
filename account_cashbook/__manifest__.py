# -*- coding: utf-8 -*-
{
    'name': "Account Cashbook",

    'summary': """
        """,

    'description': """

    """,

    'author': "SME Intellect Co. Ltd",
    'website': "https://www.smeintellect.com/",
    'category': 'Account Management',
    'version': '0.1',

    'depends': ['account',],

    'data': [

        'views/account_cashbook_view.xml',
        'views/account_move_view.xml',
        'data/ir_sequence_data.xml',
        'security/ir.access.csv',

    ],
    'license': 'LGPL-3',
}
