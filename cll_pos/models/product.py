# -*- coding: utf-8 -*-
ACCOUNT_DOMAIN = "[('account_type', 'not in', ('asset_receivable','liability_payable','asset_cash','liability_credit_card','off_balance'))]"

from odoo import api, fields, models, _

class ProductCategory(models.Model):
    _inherit = 'product.category'

    property_account_sale_categ_id = fields.Many2one('account.account', company_dependent=True,
        string="Revenue Account",
        domain=ACCOUNT_DOMAIN,
        help="This account will be used when validating a customer invoice.")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    service_transfer = fields.Boolean(
        "Transfer Service", copy=False)

    label = fields.Char(string="Label Display Name")