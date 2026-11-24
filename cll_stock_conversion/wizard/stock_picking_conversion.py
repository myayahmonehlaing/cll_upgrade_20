# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_round


class ConversionPickingLine(models.TransientModel):
    _name = "stock.conversion.picking.line"
    _rec_name = 'product_id'
    _description = 'Conversion Picking Line'

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('id', '=', product_id)]")
    quantity = fields.Float("Quantity", digits='Product Unit of Measure', required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id')
    wizard_id = fields.Many2one('stock.conversion.picking', string="Wizard")
    move_id = fields.Many2one('stock.move', "Move")
    lot_id = fields.Many2one('stock.lot', "lot")


class ConversionPicking(models.TransientModel):
    _name = 'stock.conversion.picking'
    _description = 'Conversion Picking'

    @api.model
    def default_get(self, fields):
        res = super(ConversionPicking, self).default_get(fields)
        if self.env.context.get('active_id') :
            if len(self.env.context.get('active_ids', list())) > 1:
                raise UserError(_("You may only convert one picking at a time."))
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            if picking.exists():
                res.update({'picking_id': picking.id})
        return res

    picking_id = fields.Many2one('stock.picking')
    product_conversion_moves = fields.One2many('stock.conversion.picking.line', 'wizard_id', 'Moves', compute='_compute_moves', readonly=False, store=True)
    company_id = fields.Many2one(related='picking_id.company_id')
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', domain=[('code', '=', 'mrp_operation')])

    @api.depends('picking_id')
    def _compute_moves(self):
        for wizard in self:
            product_conversion_moves = [(5,)]
            line_fields = [f for f in self.env['stock.conversion.picking.line']._fields.keys()]
            product_conversion_moves_data_tmpl = self.env['stock.conversion.picking.line'].default_get(line_fields)

            for move in wizard.picking_id.move_ids.move_line_ids:
                if move.state == 'cancel':
                    continue
                # if move.move_id.scrapped:
                #     continue

                if not move.product_id.is_convertible:
                    continue
                product_conversion_moves_data = dict(product_conversion_moves_data_tmpl)
                conversion_moves_vals = wizard._prepare_stock_conversion_picking_line_vals_from_move(move)
                if not conversion_moves_vals:
                    continue

                product_conversion_moves_data.update(conversion_moves_vals)
                product_conversion_moves.append((0, 0, product_conversion_moves_data))

            if wizard.picking_id and len(product_conversion_moves) <= 1:
                raise UserError(_("No products to convert (only lines in Done state and not fully converted yet can be converted)."))
            if wizard.picking_id:
                wizard.product_conversion_moves = product_conversion_moves
            picking_type_id = self.env['stock.picking.type'].search([('code','=','mrp_operation'),('company_id','=',wizard.company_id.id)] , limit=1)
            if picking_type_id:
                wizard.picking_type_id = picking_type_id

    @api.model
    def _prepare_stock_conversion_picking_line_vals_from_move(self, stock_move):

        quantity = stock_move.qty_done
        for conv_move in stock_move.move_id.conversion_move_ids:
            if conv_move.state == 'cancel':
                continue

            quantity -= sum(conv_ml.quantity for conv_ml in conv_move.move_line_ids
                if conv_ml.lot_id.id == stock_move.lot_id.id )

        quantity = float_round(quantity, precision_digits=0, rounding_method="UP")
        if not quantity :
           return False

        return {
            'product_id': stock_move.product_id.id,
            'quantity': quantity,
            'move_id': stock_move.move_id.id,
            'lot_id': stock_move.lot_id.id,
            'uom_id': stock_move.product_id.uom_id.id,
        }

    def _create_conversions(self):
        production = self.env['mrp.production']

        for wizard in self:
            for convert_move in wizard.product_conversion_moves:
                if not convert_move.quantity :
                    continue

                lot = self.env['stock.lot'].search([
                    ('product_id', '=', convert_move.product_id.converted_product_id.id),
                    ('name', '=', convert_move.lot_id.name)],limit=1)
                if not lot:
                    lot = convert_move.lot_id.copy({
                        'name': convert_move.lot_id.name,
                        'location_id': False,
                        'product_id': convert_move.product_id.converted_product_id.id,
                    }) if convert_move.lot_id else False
                vals = {
                    'product_id': convert_move.product_id.converted_product_id.id,
                    # 'product_uom_id': convert_move.product_id.converted_product_id.uom_id.id,
                    'origin': wizard.picking_id.name,
                    'company_id': wizard.company_id.id,
                    'date_start': fields.Date.context_today(self),
                    'date_finished': fields.Date.context_today(self),
                    'bom_id': False,
                    'picking_type_id': wizard.picking_type_id.id,
                    'location_src_id': convert_move.move_id.location_dest_id.id,
                    'location_dest_id': convert_move.move_id.location_dest_id.id,
                    'name': wizard.picking_type_id.sequence_id.next_by_id(),
                    'product_qty': convert_move.quantity,
                    'lot_producing_ids':[(4, lot.id)] if lot else False,
                    'move_raw_ids': [(0, 0, {
                        'product_id': convert_move.product_id.id,
                        'uom_id': convert_move.uom_id.id,
                        'product_uom_qty': convert_move.quantity,

                    })]

                }
                production |= self.with_context(raw_lot_id=convert_move.lot_id)._create_and_conform_mrp_production(vals)
                convert_move.move_id.write({'conversion_move_ids':[(4, m.id) for m in production.move_raw_ids] })
        return production

    def create_conversions(self):
        for wizard in self:
           production_ids = wizard._create_conversions()
        # Override the context to disable all the potential filters that could have been set previously

        return {
            'name': _('Production'),
            'view_mode': 'list,form',
            'res_model': 'mrp.production',
             'domain': [('id', 'in', production_ids.ids)],
            'type': 'ir.actions.act_window',

        }

    def _create_and_conform_mrp_production(self,vals):
        production = self.env['mrp.production'].create(vals)
        production.action_confirm()
        production.move_raw_ids._action_assign()
        production.button_mark_done()
        return production