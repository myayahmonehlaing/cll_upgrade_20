# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _


class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = 'stock.inventory.adjustment.name'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        default=lambda self: self.env.company
    )


    inventory_adjustment_name = fields.Char(default="Quantity Updated", string="Inventory Reason")

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix


    def _get_quants_context(self):
        res = super()._get_quants_context()
        res['facility'] = self.facility_id and self.facility_id.id or False
        return res

    # def action_apply(self):
    #     quants = self.quant_ids.filtered('inventory_quantity_set')
    #     return quants.with_context(inventory_name=self.inventory_adjustment_name,
    #                                facility = self.facility_id and self.facility_id.id or False).action_apply_inventory()