# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command,fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    convertible_picking = fields.Boolean("Convertible", compute ='_compute_convertible_picking')

    convert_production_ids = fields.Many2many(
        'mrp.production',
        string="Converted Manufacturing Orders",
        compute="_compute_convert_production_ids",
        store=False,
    )

    @api.depends('move_ids.conversion_move_ids')
    def _compute_convert_production_ids(self):
        for picking in self:
            picking.convert_production_ids = picking.move_ids.conversion_move_ids.mapped('raw_material_production_id')

    def _compute_convertible_picking(self):
        for picking in self:
            picking.convertible_picking = any( move.product_id.is_convertible for move in picking.move_ids)

    def _action_generate_conversion_wizard(self):
        view = self.env.ref('cll_stock_conversion.view_stock_conversion_picking_form')
        return {
            'name': _('Convert Picking?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.conversion.picking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def action_open_convert_productions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Converted Manufacturing Orders',
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.convert_production_ids.ids)],
        }


