
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, tools, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )
    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix