# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning



class AccountCashbookLine(models.Model):
    _name = "account.cashbook.line"
    _inherit = ['analytic.mixin']
    _description = "Cashbook Line"

    sequence = fields.Integer()
    name = fields.Char(required=True, string='Description',)
    cashbook_id = fields.Many2one(
        comodel_name='account.cashbook',
        string='Account Cashbook',
        required=True,
        readonly=True,
        index=True,
        ondelete="cascade",
        check_company=True,
    )
    company_id = fields.Many2one(
        related='cashbook_id.company_id', store=True, readonly=True, precompute=True,
        index=True,
    )

    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account',
        index=False,  # covered by account_move_line_account_id_date_idx defined in init()
        required=True,
        ondelete="cascade",
        domain="[('active', '=', True)]",
        check_company=True,

    )

    quantity = fields.Float(string="Quantity", default=1,required=True)
    currency_id = fields.Many2one(string="Currency", related='cashbook_id.currency_id')
    unit_price = fields.Float(string="Unit Price",required=True,default=1)
    amount = fields.Monetary(currency_field='currency_id',compute='_compute_amount' )

    @api.depends('quantity','unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.unit_price * line.quantity



