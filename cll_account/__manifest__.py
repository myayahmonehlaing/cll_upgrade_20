# -*- coding: utf-8 -*-
{
    'name': "CLL Account",

    'summary': """
        Account Advance""",

    'description': """
        Account Advance / Expense
    """,

    'author': "SME Intellect Co. Ltd",
    'website': "https://www.smeintellect.com/",
    'category': 'Account Management',
    'version': '0.1',

    'depends': ['account','hr_expense','account_asset',],

    'data': [
        'security/security.xml',
        'security/ir.access.csv',
        'views/account_move_view.xml',
        'views/hr_expense_sheet_view.xml',
        'views/account_asset_view.xml',
        'views/res_partner_views.xml',
        'views/res_config_setting_view.xml',
        'views/report_invoice.xml',
        'views/account_analytic_plan_views.xml',
        'data/ir_sequence_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cll_account/static/src/css/account_advance.css',
            'cll_account/static/src/components/**/*',
        ],
    },

    'license': 'LGPL-3',
}
