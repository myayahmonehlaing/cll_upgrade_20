# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, Command



class AccountCashbook(models.Model):
    _inherit = "account.cashbook"

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )
    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix


    def _prepare_move(self,  force_balance=None, line_ids=None):
        vals = super()._prepare_move(force_balance=force_balance, line_ids=line_ids)
        if self.facility_id:
            vals['facility_id'] = self.facility_id.id

        return vals