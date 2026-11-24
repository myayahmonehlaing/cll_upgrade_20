# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,Command, fields, models, _
from odoo.tools import formatLang
from odoo.exceptions import UserError
from odoo.tools import float_compare

class AccountMove(models.Model):
    _inherit = "account.move"

    is_employee_advance = fields.Boolean("Is Employee Advance")
    is_vendor_advance = fields.Boolean("Is Vendor Advance",index=True)
    hr_expense_sheet_count = fields.Integer("Expense Sheet Count" , compute='_compute_hr_expense_sheet_count',)
    refund_move_id = fields.Many2one('account.move', 'Related Advance')
    move_count = fields.Integer(compute='_compute_refund_count')
    refund_move = fields.Integer(compute='_compute_is_refund')
    vendor_advance_widget = fields.Json(
        compute='_compute_vendor_advance_widget_info',
        exportable=False,
    )
    total_advance_amount = fields.Monetary(
        string="Total Advance Amount",
        compute="_compute_total_advance_amount",
        readonly=True
    )
    advance_payable_balance = fields.Monetary(
        string="Total Advance Balance",
        compute="_compute_total_advance_amount",
        readonly=True
    )
    origin = fields.Char(string="Source Document")

    @api.constrains('amount_total_signed', 'advance_order_id','currency_id')
    def _check_advance_amount(self):
        for move in self.filtered('advance_order_id'):
            if move.currency_id != move.advance_order_id.currency_id:
                raise UserError(_('Currency must be the same with Purchase Order.'))

            vendor_advances = move._get_advance_moves(move.advance_order_id) - move
            total_advance_amount = abs(
                    sum(a.amount_total_in_currency_signed for a in vendor_advances)
                    + move.amount_total_in_currency_signed
            )
            if float_compare(
                    total_advance_amount,
                    move.advance_order_id.amount_total,
                    precision_rounding=move.advance_order_id.currency_id.rounding,
            ) > 0:
                raise UserError(
                    _('Total advance (%.2f) exceeds Purchase Order amount (%.2f).')
                    % (total_advance_amount, move.advance_order_id.amount_total)
                )

    @api.depends('move_type', 'state', 'line_ids.purchase_line_id.order_id')
    def _compute_total_advance_amount(self):
        for move in self:
            total_advance = 0.0
            balance = 0.0
            if (move.is_invoice(include_receipts=True)
                    and not move.is_vendor_advance
                        and not move.is_employee_advance):
                vendor_advances = move._get_all_vendor_advance_bill()
                if vendor_advances:
                    total_advance = sum(a.amount_total_in_currency_signed for a in vendor_advances)
                    purchase = move.line_ids.mapped('purchase_line_id.order_id')[:1]
                    if purchase:
                        balance = purchase.amount_total + total_advance

            move.total_advance_amount = total_advance
            move.advance_payable_balance = balance

    @api.depends('move_type', 'state', 'total_advance_amount')
    def _compute_vendor_advance_widget_info(self):
        for move in self:
            if (not move.is_invoice(include_receipts=True)
                    and not move.is_vendor_advance
                        and not move.is_employee_advance):
                move.vendor_advance_widget = False
                continue

            vendor_advances = move.sudo()._get_all_vendor_advance_bill()

            if not vendor_advances:
                move.vendor_advance_widget = False
                continue

            content = []
            for advance in vendor_advances:
                amount =  -1 * advance.amount_total_in_currency_signed
                content.append({
                    'name': advance.name,
                    'journal_name': advance.journal_id.name,
                    'amount': amount,
                    'currency_id': advance.currency_id.id,
                    'date': advance.date,
                    'ref': advance.ref,
                    'payment_state': advance._fields['payment_state'].convert_to_export(
                        advance.payment_state, advance
                    ),
                    'move_id': advance.id,
                    'amount_company_currency': formatLang(
                        self.env, amount, currency_obj=advance.currency_id
                    ),
                })

            move.vendor_advance_widget = {
                'title': _('Vendor Advance'),
                'content': content,
                'advance_balance': move.currency_id.format(move.advance_payable_balance),
            }

    def _get_all_vendor_advance_bill(self):
        purchase_order_id = self.line_ids.purchase_line_id.order_id
        if purchase_order_id:
            return self._get_advance_moves(purchase_order_id[0])
        return []
    def _get_advance_moves(self,purchase):
        return self.search([('advance_order_id', '=', purchase.id),
                     ('partner_id', '=', self.partner_id.id),
                     ('is_vendor_advance', '=', True),
                     ('move_type', 'in', ['in_invoice', 'in_refund']),
                     ('state', '=', 'posted')])

    def action_open_advance_move(self):
        self.ensure_one()
        name = _("Vendor Advance")
        res_model = 'account.move'
        res_id = self.id
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': res_model,
            'res_id': res_id,
            'target': 'current',
        }

    @api.depends('refund_move_id')
    def _compute_refund_count(self):
        for record in self:
            record.move_count = self.env['account.move'].search_count([('refund_move_id', '=', record.id),('move_type', '=', 'in_refund')])

    def bill_credit_note(self):
        credit_notes = self.env['account.move'].search([('refund_move_id', '=', self.id)])
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Credit Notes',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', credit_notes.ids)],
            'context': {
                'search_default_refund_move_id': self.id,
                'default_refund_move_id': self.id
            }
        }

        return action

    @api.depends('refund_move_id')
    def _compute_is_refund(self):
        for record in self: record['refund_move'] = self.env['account.move'].search_count(
            [('refund_move_id', '=', record.id),('move_type', '=', 'in_refund')])

    def _compute_hr_expense_sheet_count(self):
        for record in self:
            record.hr_expense_sheet_count = self.env['hr.expense.sheet'].search_count(
            [('advance_id', '=', record.id)])

    def _create_cogs_lines(self):
        if not self.company_id.right_sale:
            return super()._create_cogs_lines()
        return False


class AccountMoveName(models.TransientModel):
    _inherit = 'account.move.reversal'

    def _prepare_default_reversal(self, move):
        result = super()._prepare_default_reversal(move)
        result.update({'refund_move_id': move.id,'is_employee_advance':False})
        return result




