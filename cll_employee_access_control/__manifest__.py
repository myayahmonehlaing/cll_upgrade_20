# -*- coding: utf-8 -*-
{
    'name': "Employee Access Control",

    'summary': "Employee Access Control customization for CLL",

    'description': """
      User Request form customization for CLL
    """,

    'author': "SMEi",
    'website': "https://www.smeintellect.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail','cll_hr','cll_base_approval_rule'],

    # always loaded
    'data': [
        "data/ir_sequence_data.xml",
        "data/mail_activity_data.xml",
        "data/mail_template_data.xml",
        "security/security.xml",
        "security/ir.access.csv",
        "views/system_tag_views.xml",
        "views/system_views.xml",
        "views/application_views.xml",
        "views/employee_access_request_views.xml",
        "views/employee_handover_request_views.xml",
        "views/employee_system_overview_views.xml",
        "views/group_views.xml",
        "views/hr_asset_request_views.xml",
        "views/menus.xml",
        "views/hr_employee_views.xml",
        "report/report_template_system_overview.xml",
        "data/dashboard.xml",
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',

}

