# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""Sale Order: Provider billing and fee handling extension.

This module extends the Sale Order model to automatically generate
provider bills and compute provider fees based on defined fee policies.
"""

from odoo import api, fields, models, _
from odoo.exceptions import  UserError
from collections import defaultdict

class SaleOrder(models.Model):
    """Extend Sale Orders to handle provider billing and fee computation."""
    _inherit = 'sale.order'

    provider_bill_ids = fields.Many2many("account.move",string="Provider Bills",copy=False)
    provider_bill_count = fields.Integer(string="Bill Count", compute='_get_provider_billed')

    @api.depends('provider_bill_ids')
    def _get_provider_billed(self):
        for order in self:
            order.provider_bill_count = len(order.provider_bill_ids)


    def action_view_provider_bill(self):
        bills = self.mapped('provider_bill_ids')
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_out_invoice_type')
        if len(bills) > 1:
            action['domain'] = [('id', 'in', bills.ids)]
        elif len(bills) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view)
                        for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = bills.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        action['context'] =  {
            'default_move_type': 'in_invoice',
        }
        return action


    def action_confirm(self,**kwargs ):
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        super().action_confirm()
        for order in self:
            provider_sign = defaultdict(list)
            for line in  order.order_line.filtered(lambda x: x.provider_id):
                sign = -1 if line.price_subtotal < 0 else 1
                provider_sign[(line.provider_id, sign)].append(line)

            if order.provider_bill_ids or not provider_sign:
                continue

            for (provider, sign), lines in provider_sign.items():
                kwargs.update({
                    'provider_id': provider,
                    'sign': sign,
                    'order_lines':lines
                })
                invoice_vals = order._prepare_provider_invoice(**kwargs)
                if not invoice_vals:
                    continue

                move = (AccountMove.sudo().with_company(invoice_vals['company_id'])
                        .create(invoice_vals))
                move.action_post()
                order.provider_bill_ids = [(4, move.id)]

    def _prepare_account_move_line(self,**kwargs):
        self.ensure_one()
        return [ vals for vals in (
                l._get_provider_fee(kwargs.get('provider_id'))
                for l in kwargs.get('order_lines')
            ) if vals ]

    def _prepare_provider_invoice(self,**kwargs):
        """Prepare the dict of values to create the new bill.
        """
        self.ensure_one()
        move_line_vals_list = self._prepare_account_move_line(**kwargs)

        if not move_line_vals_list :
            return False
        provider_id = kwargs.get('provider_id')
        sign = kwargs.get('sign')
        partner_bank_id = provider_id.commercial_partner_id.bank_ids.filtered_domain(
            ['|', ('company_id', '=', False),
             ('company_id', '=', self.company_id.id)])[:1]
        move_type = 'in_invoice' if sign == 1  else 'in_refund'
        return  {
            'ref': self.name ,
            'move_type': move_type,
            'invoice_date': fields.Date.context_today(self),
            'currency_id': self.company_id.currency_id.id,
            'partner_id': provider_id.id,
            'partner_bank_id': partner_bank_id.id,
            'invoice_origin': self.name,
            'company_id': self.company_id.id,
            'facility_id': self.facility_id.id,
            'invoice_payment_term_id': provider_id.property_payment_term_id.id,
            'invoice_line_ids': [(0, 0, line) for line in move_line_vals_list],
        }


class SaleOrderLine(models.Model):
    """Extend Sale Order Lines to calculate provider-specific fees."""
    _inherit = 'sale.order.line'

    provider_id = fields.Many2one(comodel_name='res.partner', string="Provider")


    def _get_provider_fee(self, provider_id):
        policy_line = self.env['provider.fee.policy.line'].search([
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.company_id.id),
            ('policy_id.partner_id', '=', provider_id.id)
        ], limit=1)

        if not self.price_subtotal or ( provider_id and not policy_line ) :
            return False

        return {
            'display_type': 'product',
            'product_id': self.product_id.id,
            'name': f'{self.product_id.display_name} (Provider Fee)',
            'quantity': 1,
            'price_unit': ( abs(self.price_subtotal) * policy_line.percent if policy_line.percent
                        else policy_line.amount or 0 ) ,
            'account_id': policy_line.account_id.id if policy_line.account_id else False,
            'analytic_distribution': self.analytic_distribution,
        }


    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line( **optional_values)
        if self.provider_id:
            res['provider_id'] = self.provider_id.id
        return res
