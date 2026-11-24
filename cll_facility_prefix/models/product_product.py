# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )

    def _get_filtered_supplier(self, company_id, product_id, params=False):
        if self.env.context.get('facility_id'):
            facility_id = self.env.context.get('facility_id').id
            return self.filtered(lambda s: (s.facility_id.id == facility_id) and (not s.company_id or s.company_id.id == company_id.id)
                                           and (s.partner_id.active and (not s.product_id or s.product_id == product_id)) )

        return self.filtered(lambda s: (not s.company_id or s.company_id.id == company_id.id)  and (s.partner_id.active and (not s.product_id or s.product_id == product_id)))
