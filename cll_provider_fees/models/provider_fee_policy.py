# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command,fields, models, _
from odoo.exceptions import ValidationError

class ProviderFeePolicy(models.Model):
    _name = "provider.fee.policy"
    _description = "Provider Fee"

    name = fields.Char(string="Name", copy=False ,compute='_compute_name',  store=True)
    partner_id = fields.Many2one('res.partner', string="Provider", required=True, domain=[('is_provider', '=', True)])
    company_id = fields.Many2one('res.company', string="Company", required=True,default=lambda self: self.env.company)
    line_ids = fields.One2many('provider.fee.policy.line','policy_id',string = 'Fees Lines')

    @api.constrains("partner_id", "company_id")
    def _check_partner_company_unique(self):
        for record in self:
            if not record.partner_id:
                continue

            if self.search_count([
                ("id", "!=", record.id),
                ("partner_id", "=", record.partner_id.id),
                ("company_id", "=", record.company_id.id),
            ]):
                raise ValidationError(
                    _("Policy Provider must be unique per company!")
                )

    @api.depends('partner_id')
    def _compute_name(self):
        for record in self:
            record.name = record.partner_id.name

class ProviderFeePolicyLine(models.Model):
    _name = "provider.fee.policy.line"
    _description = "Provider Fee Lines"

    policy_id = fields.Many2one('provider.fee.policy', string="Policy")
    product_id = fields.Many2one('product.product',string="Product")
    amount = fields.Monetary(string="Amount",)
    percent = fields.Float(string="Percentage")
    account_id = fields.Many2one('account.account', string="COGS Account", )
    company_id = fields.Many2one('res.company', string="Provider", related='policy_id.company_id',store=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        store=True,

    )

    @api.constrains("product_id", "policy_id")
    def _check_product_policy_unique(self):
        for record in self:
            if not record.product_id or not record.policy_id:
                continue

            if self.search_count([
                ("id", "!=", record.id),
                ("product_id", "=", record.product_id.id),
                ("policy_id", "=", record.policy_id.id),
            ]):
                raise ValidationError(
                    _("Product must be unique per policy!")
                )

    @api.constrains('amount', 'percent')
    def _check_amount_percent(self):
        for record in self:
            if ((record.amount == 0 and record.percent == 0)
                    or (record.amount > 0 and record.percent > 0)):
                raise ValidationError("Either Amount or Percent must be greater than zero — not both or neither.")

