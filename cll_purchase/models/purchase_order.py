# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command,fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    partner_id = fields.Many2one('res.partner', domain="[('is_vendor', '=', True)]")
    attachment_ids = fields.Many2many('ir.attachment', string='Purchase Attachments')
    is_subcontract = fields.Boolean("Is Subcontract?")
    refer_specific = fields.Char(string='Refer Specific Source')
    vendor_advance_count = fields.Integer(compute='_compute_vendor_advance_count')

    def _compute_vendor_advance_count(self):
        for order in self:
            order.vendor_advance_count = self.env['account.move'].search_count(
                [('advance_order_id', '=', order.id), ('move_type', '=', 'in_invoice')])

    def action_open_vendor_advance(self):
        vendor_advances = self.env['account.move'].search([('advance_order_id', '=', self.id)])
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Advance',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', vendor_advances.ids)],
            'context': {
                'search_default_advance_order_id': self.id,
                'default_advance_order_id': self.id,
                'default_facility_id': self.facility_id.id if self.facility_id else False,
                'default_is_vendor_advance': True,
                'default_currency_id': self.currency_id.id,
            }
        }

        return action

    def button_approval_request(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.approval.request',
            'view_mode': 'form',
            'target': 'new',
        }

    def _prepare_invoice(self):
        result = super()._prepare_invoice()
        result['move_attachment_ids'] = [(6, 0, self.attachment_ids.ids )]
        return result

    def _prepare_picking(self):
        result = super()._prepare_picking()
        result['attachment_ids'] = [(6, 0, self.attachment_ids.ids)]
        return result


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    expired_date = fields.Date("Expired Date")
    procurement_note = fields.Char("Procurement Note")

    def _prepare_account_move_line(self, move=False):
        result = super()._prepare_account_move_line(move)
        result['name'] =  self.name
        return result



