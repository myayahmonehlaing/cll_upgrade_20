# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix

    @api.model_create_multi
    def create(self, vals_list):
        res =  super().create(vals_list)
        if res and res.facility_id:
            res.name = res.facility_id.code + '/' + res.name
        return res

    def write(self, values):
        result = super().write(values)
        if self.request_status == 'new' and 'facility_id' in values and self.facility_id :
            self.name = self.facility_id.code + '/' + self.name[5:len(self.name)]
        return result