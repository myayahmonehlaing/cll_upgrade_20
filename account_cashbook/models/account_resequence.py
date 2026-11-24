# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ReSequenceWizard(models.TransientModel):
    _inherit = 'account.resequence.wizard'


    @api.model
    def default_get(self, fields_list):
        # values = super(ReSequenceWizardInhert, self).default_get(fields_list)
        values =  {'ordering': 'keep'}
        if 'move_ids' not in fields_list:
            return values
        active_move_ids = self.env['account.move']
        if self.env.context['active_model'] == 'account.move' and 'active_ids' in self.env.context:
            active_move_ids = self.env['account.move'].browse(self.env.context['active_ids'])
        if len(active_move_ids.journal_id) > 1:
            raise UserError(_('You can only resequence items from the same journal'))
        move_types = set(active_move_ids.mapped('move_type'))
        if (
            active_move_ids.journal_id.refund_sequence
            and ('in_refund' in move_types or 'out_refund' in move_types)
            and len(move_types) > 1
        ):
            raise UserError(_('The sequences of this journal are different for Invoices and Refunds but you selected some of both types.'))
        is_payment = set(active_move_ids.mapped(lambda x: bool(x.origin_payment_id or x.cashbook_id)))
        if (
            active_move_ids.journal_id.payment_sequence
            and len(is_payment) > 1
        ):
            raise UserError(_('The sequences of this journal are different for Payments and non-Payments but you selected some of both types.'))
        values['move_ids'] = [(6, 0, active_move_ids.ids)]
        return values