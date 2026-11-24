# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models, SUPERUSER_ID


class PurchaseMakeInv(models.TransientModel):
    _name = 'purchase.make.inv'
    _description = "Purchase Make Invoice"

    count = fields.Integer(string="Order Count", compute='_compute_count')
    purchase_order_ids = fields.Many2many(
        'purchase.order', default=lambda self: self.env.context.get('active_ids'))

    consolidated_billing = fields.Boolean(
        string="Consolidated Billing", default=True,
        help="Create one bill for all orders related to same vendor and same billing address"
    )

    #=== COMPUTE METHODS ===#

    @api.depends('purchase_order_ids')
    def _compute_count(self):
        for wizard in self:
            wizard.count = len(wizard.purchase_order_ids)


    def create_invoices(self):
        invoices = self._create_invoices(self.purchase_order_ids)
        return self.purchase_order_ids.action_view_invoice(invoices=invoices)