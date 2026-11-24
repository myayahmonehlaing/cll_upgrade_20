# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command,fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"

    conversion_move_ids = fields.Many2many(
        'stock.move', 'stock_move_conversion_rel', 'move_orig_id', 'move_production_id', 'Moves',
        copy=False,
        help="Optional: next stock move when chaining them")

    def _update_reserved_quantity(self, need, location_id, lot_id=None, package_id=None, owner_id=None,
                                  strict=True):
        self.ensure_one()
        if self.env.context.get('raw_lot_id'):
            lot_id = self.env.context.get('raw_lot_id')
        return super()._update_reserved_quantity(
            need,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )




