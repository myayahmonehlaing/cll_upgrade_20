# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    pos_order_id = fields.Many2one(
        related="pos_line_id.order_id", string="POS Order", store=True, readonly=True
    )
    pos_line_id = fields.Many2one(
        "pos.order.line", string="Origin POS Item", index="btree_not_null", copy=False
    )
