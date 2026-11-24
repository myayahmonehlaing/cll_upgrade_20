# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, Command, models, _
from odoo.tools import email_split, float_repr, float_round, is_html_empty


class HrExpense(models.Model):
    _inherit = "hr.expense"

    currency_rate = fields.Float(compute='_compute_currency_rate', digits=(16, 2), readonly=False, tracking=True, )
    label_currency_rate = fields.Char(compute='_compute_currency_rate', readonly=True)

    @api.depends('quantity', 'price_unit', 'tax_ids', 'currency_rate')
    def _compute_total_amount_currency(self):
        AccountTax = self.env['account.tax']
        for expense in self.filtered('product_has_cost'):
            base_line = expense._prepare_base_line_for_taxes_computation(
                price_unit=expense.price_unit * expense.currency_rate, quantity=expense.quantity)
            AccountTax._add_tax_details_in_base_line(base_line, expense.company_id)
            AccountTax._round_base_lines_tax_details([base_line], expense.company_id)
            expense.total_amount_currency = base_line['tax_details']['total_included_currency']

    @api.depends('currency_id', 'total_amount_currency', 'date')
    def _compute_currency_rate(self):
        """
            We want the default odoo rate when the following change:
            - the currency of the expense
            - the total amount in foreign currency
            - the date of the expense
            this will cause the rate to be recomputed twice with possible changes but we don't have the required fields
            to store the override state in stable
        """
        date_today = fields.Date.context_today(self)
        for expense in self:
            if expense.is_multiple_currency:
                if (
                        expense.currency_id != expense._origin.currency_id
                        or expense.total_amount_currency != expense._origin.total_amount_currency
                        or expense.date != expense._origin.date
                ):
                    expense._set_expense_currency_rate(date_today=date_today)
                else:
                    expense.currency_rate = expense.total_amount / expense.total_amount_currency if expense.total_amount_currency else 1.0
            else:  # Mono-currency case computation shortcut, no need for the label if there is no conversion
                expense.currency_rate = 1.0
                expense.label_currency_rate = False
                continue

            company_currency = expense.company_currency_id or expense.env.company.currency_id
            expense.label_currency_rate = _(
                '1 %(exp_cur)s = %(rate)s %(comp_cur)s',
                exp_cur=(expense.currency_id or company_currency).name,
                rate=float_repr(expense.currency_rate, 6),
                comp_cur=company_currency.name,
            )


# class HrExpenseSheet(models.Model):
#     _inherit = "hr.expense.sheet"
#
#     total_amount = fields.Monetary(
#         string="Total",
#         currency_field='currency_id',
#         compute='_compute_amount', store=True, readonly=True,
#         tracking=True,
#     )
#     untaxed_amount = fields.Monetary(
#         string="Untaxed Amount",
#         currency_field='currency_id',
#         compute='_compute_amount', store=True, readonly=True,
#     )
#     total_tax_amount = fields.Monetary(
#         string="Taxes",
#         currency_field='currency_id',
#         compute='_compute_amount', store=True, readonly=True,
#     )
#     amount_residual = fields.Monetary(
#         string="Amount Due",
#         currency_field='currency_id',
#         compute='_compute_from_account_move_ids', store=True, readonly=True,
#     )
#
#     currency_rate = fields.Float(compute='_compute_currency_rate', readonly=False,
#                                  store=True, precompute=True)
#
#     @api.depends('expense_line_ids.currency_id', 'expense_line_ids.currency_rate')
#     def _compute_currency_rate(self):
#         for sheet in self:
#             if sheet.expense_line_ids :
#                 sheet.currency_rate = sheet.expense_line_ids[:1].currency_rate
#             else:
#                 sheet.currency_rate = 1 / self.env['res.currency']._get_conversion_rate(
#                     from_currency=sheet.company_currency_id,
#                     to_currency=sheet.currency_id,
#                     company=sheet.company_id,
#                     date=fields.Date.context_today(self),
#                 )
#
#     @api.depends('expense_line_ids.total_amount', 'expense_line_ids.tax_amount','expense_line_ids.total_amount_currency', 'expense_line_ids.tax_amount_currency')
#     def _compute_amount(self):
#         for sheet in self:
#             sheet.total_amount = sum(sheet.expense_line_ids.mapped('total_amount_currency'))
#             sheet.total_tax_amount = sum(sheet.expense_line_ids.mapped('tax_amount_currency'))
#             sheet.untaxed_amount = sheet.total_amount - sheet.total_tax_amount
#
#     @api.depends('expense_line_ids.currency_id', 'company_currency_id')
#     def _compute_currency_id(self):
#         for sheet in self:
#             if sheet.is_multiple_currency :
#                 sheet.currency_id = sheet.expense_line_ids[:1].currency_id
#             elif not sheet.expense_line_ids or sheet.payment_mode == 'own_account' :
#                 sheet.currency_id = sheet.company_currency_id
#
#     def _prepare_move_vals(self):
#         vals = super()._prepare_move_vals()
#         vals['currency_rate'] = self.currency_rate
#         return vals


