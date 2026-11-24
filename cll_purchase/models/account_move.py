# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command,fields, models, _
from odoo.tools import formatLang

class AccountMove(models.Model):
    _inherit = "account.move"

    move_attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    advance_order_id = fields.Many2one("purchase.order", "Advance Purchase Order",index=True)

    partner_advance_warning = fields.Text(
        compute='_compute_partner_advance_warning',
    )

    @api.depends('company_id', 'advance_order_id', 'currency_id')
    def _compute_partner_advance_warning(self):
        for move in self:
            warning_msg = ''

            if move.is_vendor_advance and move.advance_order_id:
                invoices = move.advance_order_id.mapped('order_line.invoice_lines.move_id').filtered(
                    lambda m: m.payment_state == 'paid'
                )
                if invoices:
                    invoices_names = ", ".join(invoices.mapped('name'))
                    total_amount = sum(invoices.mapped('amount_total_in_currency_signed'))
                    warning_msg = _(
                        '%(po_name)s has %(invoices_name)s in paid state. Total: %(total_amount)s',
                        po_name=move.advance_order_id.name,
                        invoices_name=invoices_names,
                        total_amount=formatLang(self.env, abs(total_amount), currency_obj=move.currency_id)
                    )

            move.partner_advance_warning = warning_msg

    @api.depends('line_ids.purchase_line_id','advance_order_id')
    def _compute_origin_po_count(self):
        for move in self:
            move.purchase_order_count = len(move.line_ids.purchase_line_id.order_id) or len(move.advance_order_id)

    def action_view_source_purchase_orders(self):
        self.ensure_one()
        source_orders = self.line_ids.purchase_line_id.order_id or self.advance_order_id
        result = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_form_action')
        if len(source_orders) > 1:
            result['domain'] = [('id', 'in', source_orders.ids)]
        elif len(source_orders) == 1:
            result['views'] = [(self.env.ref('purchase.purchase_order_form', False).id, 'form')]
            result['res_id'] = source_orders.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result