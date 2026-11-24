# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import SUPERUSER_ID, _, api, fields, models, registry

class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'stock.rule'

    # def _push_prepare_move_copy_values(self, move_to_copy, new_date):
    #     new_move_vals = super()._push_prepare_move_copy_values(move_to_copy,new_date)
    #     new_move_vals['note'] = move_to_copy.picking_id.note
    #     return new_move_vals
