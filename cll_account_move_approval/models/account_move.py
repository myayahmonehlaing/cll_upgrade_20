# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""
This module extends the account.move model to implement an approval workflow
for employee advances, including approver tracking, approval states,
and activity scheduling.
"""

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

class AccountMove(models.Model):
    """
      Extend account.move to add multi-level approval workflow for employee advance payments.
      Manages approvers, approval states, and related activities.
      """
    _name = "account.move"
    _inherit = ["account.move", "approval.mixin"]

    employee_advance_approval_activity =  'cll_account_move_approval.mail_activity_data_advance_approval'
    vendor_advance_approval_activity = 'cll_account_move_approval.mail_activity_data_vendor_advance_approval'
    bill_approval_activity = 'cll_account_move_approval.mail_activity_data_bill_approval'

    state = fields.Selection(
        selection_add=[
            ('submit', 'To Approve'),
            ('approve', 'Approved'),
            ('posted',),
            ('refuse', 'Refused'),
            ('cancel',),
        ],
        ondelete={
            'submit': 'set default',
            'approve': 'set default',
            'refuse': 'set default',
        },
    )

    invoice_has_outstanding = fields.Boolean(
        groups="account.group_account_invoice,account.group_account_readonly,cll_account_move_approval.post_and_register_payment_permission_group",
        compute='_compute_invoice_has_outstanding',
    )

    @api.depends('payment_state', 'state', 'is_move_sent')
    def _compute_status_in_payment(self):
        for move in self:
            if move.state == 'posted':
                if move.payment_state in ('partial', 'in_payment', 'paid', 'reversed'):
                    move.status_in_payment = move.payment_state
                elif move.is_move_sent:
                    move.status_in_payment = 'sent'
            elif move.state == 'draft':
                if move.payment_state in ('partial', 'in_payment', 'paid'):
                    move.status_in_payment = move.payment_state
            elif move.state in ('submit','approve','refuse'):
                move.status_in_payment = 'draft'
            if not move.status_in_payment:
                move.status_in_payment = move.state


    @api.model
    def default_get(self, fields_list):
        """Overwrite for default value of company setting approval usage flag"""
        res = super().default_get(fields_list)
        if "use_approval" in fields_list:
            use_approval = False
            if self.env.context.get('default_move_type') == 'in_invoice':
                if (self.env.company.advance_approval
                        and self.env.context.get('default_is_employee_advance')
                ) or (self.env.company.vendor_advance_approval
                        and self.env.context.get('default_is_vendor_advance')
                ) or (self.env.company.bill_approval
                        and not self.env.context.get('default_is_employee_advance')
                      and not self.env.context.get('default_is_vendor_advance')
                ):
                    use_approval = True
            res["use_approval"] = use_approval
        return res

    def action_submit(self):
        """Action to submit advance for approval."""
        for move in self:
            move.process_approval_create(amount=-move.amount_total_in_currency_signed)
            move.state = "submit"


    def _compute_use_approval(self):
        """Compute whether to use approval workflow based on company settings"""
        for record in self:
            use_approval = False
            if  record.move_type == 'in_invoice' :
                if ( record.company_id.bill_approval and not record.is_employee_advance and not record.is_vendor_advance)\
                        or (record.company_id.advance_approval and record.is_employee_advance )\
                        or ( record.company_id.vendor_advance_approval and record.is_vendor_advance) :
                    use_approval = True
            record.use_approval = use_approval

    @api.depends('posted_before', 'state', 'journal_id', 'date', 'move_type', 'origin_payment_id')
    def _compute_name(self):
        self = self.sorted(lambda m: (m.date, m.ref or '', m._origin.id))

        for move in self:
            if move.state == 'cancel':
                continue

            move_has_name = move.name and move.name != '/'
            if not move.posted_before and not move._sequence_matches_date():
                # The name does not match the date and the move is not the first in the period:
                # Reset to draft
                move.name = False
                continue
            if move.date and not move_has_name and move.state not in ('draft','submit'):
                move._set_next_sequence()

        self._inverse_name()

    def get_move_name(self):
        """
          Return a display name for the move, including reference if available.
          If name is '/', use 'Employee Advance' with reference.
          """
        ref = _("( Ref - %s )") % self.ref if self.ref else ''
        return self.name if self.name != '/' else f"Employee Advance {ref or ''}"

    def action_approver_approve(self):
        """Approve approval state of expense sheet report"""
        subject = f"{self.get_move_name()} has been approved"
        subtype_id = self.get_subtype()
        self.message_post_with_source(
            'cll_account_move_approval.account_move_template_approve',
            subtype_id=subtype_id,
            render_values={'ref': self.ref, 'name': self.name, 'type': self.move_type},
            subject=subject)
        # super().action_approver_approve()
        return super().action_post()

    def button_draft(self):
        refused_moves = self.filtered(lambda m: m.state == 'refuse')
        normal_moves = self - refused_moves
        if normal_moves:
            super(AccountMove, normal_moves).button_draft()
        if refused_moves:
            refused_moves._check_draftable()
            refused_moves.mapped('line_ids.analytic_line_ids').unlink()
            refused_moves.mapped('line_ids').remove_move_reconcile()
            refused_moves.state = 'draft'
        self.action_reset_approval()
        return True

    @api.depends('restrict_mode_hash_table', 'state')
    def _compute_show_reset_to_draft_button(self):
        for move in self:
            move.show_reset_to_draft_button = (
                not move.restrict_mode_hash_table \
                and ( move.state in ('cancel', 'refuse') or (move.state == 'posted' and not move.need_cancel_request))
            )

    def _get_approval_activity(self):
        self.ensure_one()
        if self.is_employee_advance:
            return self.employee_advance_approval_activity
        if self.is_vendor_advance:
            return self.vendor_advance_approval_activity
        if not self.is_vendor_advance and not self.is_employee_advance:
            return self.bill_approval_activity
        return self.approval_activity



