
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, Command


class AccountPayment(models.Model):
    _inherit = "account.payment"

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix

    def _generate_move_vals(self, write_off_line_vals=None, force_balance=None, line_ids=None):
        values = super()._generate_move_vals(write_off_line_vals, force_balance, line_ids)
        values.update({'facility_id': self.facility_id.id})
        return values


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )
    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix


    def _create_payments(self):
        payments = super()._create_payments()
        if self.facility_id:
            payments.write({"facility_id": self.facility_id.id})
        return payments


    def _get_wizard_values_from_batch(self, batch_result):
        """The method that allowed to add the analytic account to the invoice lines
        has been dropped in v13. Fortunately we can add it easily with this
        prepare method.
        """
        lines = batch_result['lines']
        res = super()._get_wizard_values_from_batch(batch_result)
        if lines.move_id.facility_id :
            res.update({"facility_id":lines.move_id.facility_id.id})

        return res




    def _create_payment_vals_from_wizard(self, batch_result):
        """The method that allowed to add the analytic account to the invoice lines
        has been dropped in v13. Fortunately we can add it easily with this
        prepare method.
        """
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.facility_id:
            payment_vals.update({"facility_id": self.facility_id.id})
        return payment_vals