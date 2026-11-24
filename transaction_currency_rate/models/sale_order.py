from contextlib import contextmanager
from odoo import api, fields, models, Command, _



class SaleOrder(models.Model):
    _inherit = "sale.order"

    currency_rate = fields.Float(
        compute='_compute_currency_rate', inverse='_inverse_currency_rate',
        help="Currency rate from company currency to document currency.",store=True,
    )

    is_multiple_currency = fields.Boolean(
        string="Is currency_id different from the company_currency_id",
        compute='_compute_is_multiple_currency',
    )

    @api.depends('currency_id', 'date_order', 'company_id')
    def _compute_currency_rate(self):
        for order in self:
            order.currency_rate = 1 / self.env['res.currency']._get_conversion_rate(
                from_currency=order.company_id.currency_id,
                to_currency=order.currency_id,
                company=order.company_id,
                date=(order.date_order or fields.Datetime.now()).date(),
            )

    @api.depends('currency_id')
    def _inverse_currency_rate(self):
        pass

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'currency_rate': self.currency_rate,
        })
        return invoice_vals


    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_is_multiple_currency(self):
        for order in self:
            order.is_multiple_currency = order.currency_id != order.company_id.currency_id



