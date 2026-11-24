# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, Command, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby


class StockMove(models.Model):
    _inherit = "stock.move"

    description = fields.Char(string="Remark")

    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a new
        picking to assign them to. """
        Picking = self.env['stock.picking']
        grouped_moves = groupby(self, key=lambda m: m._key_assign_picking())
        for _group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*moves)
            new_picking = False
            # Could pass the arguments contained in group but they are the same
            # for each move that why moves[0] is acceptable
            # picking = moves[0]._search_picking_for_assignation()
            # if picking:
            #     # If a picking is found, we'll append `move` to its move list and thus its
            #     # `partner_id` and `ref` field will refer to multiple records. In this
            #     # case, we chose to wipe them.
            #     vals = moves._assign_picking_values(picking)
            #     if vals:
            #         picking.write(vals)
            # else:
            #     # Don't create picking for negative moves since they will be
            #     # reverse and assign to another picking
            moves = moves.filtered(lambda m: m.uom_id.compare(m.product_uom_qty, 0.0) >= 0)
            if not moves:
                continue
            new_picking = True
            picking = Picking.create(moves._get_new_picking_values())

            moves.write({'picking_id': picking.id})
            moves._assign_picking_post_process(new=new_picking)
        return True


    def _get_new_picking_values(self):
        """ return create values for new picking that will be linked with group
        of moves in self.
        """
        pickings = self.move_orig_ids.mapped('picking_id')
        res = super(StockMove, self)._get_new_picking_values()
        if pickings :
            res['note']=  ', '.join([picking.note if picking.note else '' for picking in pickings])
        return res

    def _update_reserved_quantity_vals(self, need, location_id, lot_id=None, package_id=None, owner_id=None,
                                       strict=True):
        if self.sale_line_id.lot_id and not lot_id:
            lot_id = self.sale_line_id.lot_id
        move_line_vals, taken_quantity = super()._update_reserved_quantity_vals(need, location_id, lot_id, package_id, owner_id, strict)
        return move_line_vals, taken_quantity


    def _should_create_account_move(self):
        """Determines if an account move should be created for this move.
        :return: True if an account move should be created, False otherwise.
        """
        self.ensure_one()
        location_move = (self.location_dest_id.valuation_account_id or self.location_id.valuation_account_id)
        if self.company_id.right_sale:
            location_move = ( location_move or (self.location_dest_id.usage == 'customer' or self.location_id.usage == 'customer'))

        return self.product_id.is_storable and self.is_valued   and location_move \
            and not self.uom_id.is_zero(self.quantity) \
            and self.product_id.valuation == 'real_time'


    def _get_account_move_line_vals(self):
        vals_list = super()._get_account_move_line_vals()
        if self.company_id.right_sale:
            accounts = self.product_id._get_product_accounts()
            if self.location_id.usage == 'customer':
                debit_acc, credit_acc = accounts['stock_valuation'], accounts['expense']
            elif self.location_dest_id.usage == 'customer':
                debit_acc, credit_acc = accounts['expense'], accounts['stock_valuation']
            else:
                return vals_list

            for vals in vals_list:
                vals['account_id'] = (credit_acc if vals['credit'] > 0 else debit_acc).id
                vals['quantity'] = self.quantity
                if vals['account_id'] ==  accounts['expense'].id:
                    vals['analytic_distribution'] = self.analytic_distribution
        return vals_list