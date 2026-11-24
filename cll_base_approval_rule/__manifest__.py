{
    "name": "Cll Base Approval Rule",
    "version": "1.0",
    "category": "Approval",
    "summary": "Base Approval Rule",
    "author": "SME Intellect Co. Ltd",
    "website": "https://www.smeintellect.com/",
    "depends": ["base", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.access.csv",
        "data/mail_activity_data.xml",
        "wizard/approver_refuse_reason_view.xml",
        "views/approval_rule_views.xml",

    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
