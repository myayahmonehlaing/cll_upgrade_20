# -*- coding: utf-8 -*-
{
    'name': "Cll Account Move Approval",

    'summary': """
        Account """,

    'description': """
       Account Move Approval
    """,

    'author': "SME Intellect Co. Ltd",
    'website': "https://www.smeintellect.com/",
    'category': 'Account Management',
    'version': '0.1',
    'depends': ['account','cll_account','cll_base_approval_rule'],

    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'data/mail_activity_data.xml',
        'views/account_move_view.xml',
        'views/res_config_setting_view.xml',

    ],
    'license': 'LGPL-3',
}
