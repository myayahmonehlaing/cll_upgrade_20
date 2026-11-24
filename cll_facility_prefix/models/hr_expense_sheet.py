# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, Command, models, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo.tools.misc import clean_context

class HrExpense(models.Model):
    _inherit = "hr.expense"

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix

    # def _get_default_expense_sheet_values(self):
    #     values = super()._get_default_expense_sheet_values()
    #     if self.facility_id:
    #         values[0]['facility_id'] = self.facility_id.id
    #         # values[0]['employee_journal_id'] = self.facility_id.expense_journal_id.id
    #     return values


# class HrExpenseSheet(models.Model):
#     _inherit = "hr.expense.sheet"
#
#     facility_id = fields.Many2one(
#         comodel_name='res.facility',
#         string="Facility",
#     )
#     use_facility = fields.Boolean(compute='_compute_use_facility')
#
#     @api.depends('company_id')
#     def _compute_use_facility(self):
#         for record in self:
#             record.use_facility = record.company_id.use_facility_code_to_determine_prefix
#
#     def _prepare_bills_vals(self):
#         values = super()._prepare_bills_vals()
#         if self.facility_id:
#             values['facility_id'] = self.facility_id.id
#         return values
