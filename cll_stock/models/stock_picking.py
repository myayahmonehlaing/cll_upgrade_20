# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models,fields,api

class StockPicking(models.Model):
    _inherit='stock.picking'

    customer_ref = fields.Char("Customer Ref",compute='_compute_customer_ref', store=True,)

    def _compute_show_lots_text(self):
        group_production_lot_enabled = self.env.user.has_groups('stock.group_production_lot')
        for picking in self:
            if not picking.move_line_ids and not picking.picking_type_id.use_create_lots:
                picking.show_lots_text = False
            elif (
                group_production_lot_enabled
                and picking.picking_type_id.use_create_lots
                and picking.picking_type_id.code == 'incoming'
                and not picking.purchase_id):
                    picking.show_lots_text = False
            elif group_production_lot_enabled and picking.picking_type_id.use_create_lots \
                    and not picking.picking_type_id.use_existing_lots and picking.state != 'done':
                picking.show_lots_text = True
            else:
                picking.show_lots_text = False

    @api.depends('move_ids')
    def _compute_customer_ref(self):
        for picking in self:
            picking.customer_ref = picking.move_ids.mapped(
                'sale_line_id').order_id.client_order_ref


