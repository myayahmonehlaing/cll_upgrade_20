# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,_
from markupsafe import Markup

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    is_from_purchase = fields.Boolean(compute='_compute_is_from_purchase')
    batch_number = fields.Char("Batch No.")
    description = fields.Char(string="Remark",readonly=False)

    def _compute_is_from_purchase(self):
        for record in self:
            record.is_from_purchase = True if self.picking_id.purchase_id else False

    def create(self, vals_list):
        records = super().create(vals_list)

        for vals, line in zip(vals_list, records):
            if 'quant_id' not in vals:
                continue

            picking = line.picking_id
            if not picking:
                continue

            lot_name = line.lot_id.name or '-'

            picking.message_post(
                body=_(
                    "Lot/Serial Set: %s (%s)"
                ) % (
                         line.product_id.display_name,
                         lot_name,
                     )
            )

        return records

    def write(self, vals):
        old_lots = {}

        if 'quant_id' in vals:
            for line in self:
                old_lots[line.id] = line.lot_id.name if line.lot_id else '-'
        res = super().write(vals)

        if 'quant_id' in vals:
            for line in self:
                picking = line.picking_id
                if not picking:
                    continue

                old_lot = old_lots.get(line.id, '-')
                new_lot = line.lot_id.name or '-'
                if old_lot != new_lot:
                    picking.message_post(
                        body=_(
                            "Lot/Serial Changed: %s (%s → %s)"
                        ) % (
                                 line.product_id.display_name,
                                 old_lot,
                                 new_lot,
                             )
                    )
        return res