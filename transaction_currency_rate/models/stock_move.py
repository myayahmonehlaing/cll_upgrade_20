# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, tools, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockMove(models.Model):
    _inherit = "stock.move"


    # def _get_price_unit(self):
    #     """ Returns the unit price for the move"""
    #     self.ensure_one()
    #     if self._should_ignore_pol_price():
    #         return super(StockMove, self)._get_price_unit()
    #     price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
    #     line = self.purchase_line_id
    #     order = line.order_id
    #     date = self.env.context.get('force_period_date') or fields.Date.context_today(self)  # yahmone
    #     received_qty = line.qty_received
    #     if self.state == 'done':
    #         received_qty -= self.product_uom._compute_quantity(self.quantity, line.product_uom,
    #                                                            rounding_method='HALF-UP')
    #     if line.product_id.purchase_method == 'purchase' and float_compare(line.qty_invoiced, received_qty,
    #                                                                        precision_rounding=line.product_uom.rounding) > 0:
    #         move_layer = line.move_ids.sudo().stock_valuation_layer_ids
    #         invoiced_layer = line.sudo().invoice_lines.stock_valuation_layer_ids
    #         # value on valuation layer is in company's currency, while value on invoice line is in order's currency
    #         receipt_value = 0
    #         if move_layer:
    #             receipt_value += sum(move_layer.mapped(lambda l: l.currency_id._convert(
    #                 l.value, order.currency_id, order.company_id, l.create_date, round=False)))
    #         if invoiced_layer:
    #             receipt_value += sum(invoiced_layer.mapped(lambda l: l.currency_id._convert(
    #                 l.value, order.currency_id, order.company_id, l.create_date, round=False)))
    #         total_invoiced_value = 0
    #         invoiced_qty = 0
    #         for invoice_line in line.sudo().invoice_lines:
    #             if invoice_line.move_id.state != 'posted':
    #                 continue
    #             # Adjust unit price to account for discounts before adding taxes.
    #             adjusted_unit_price = invoice_line.price_unit * (
    #                         1 - (invoice_line.discount / 100)) if invoice_line.discount else invoice_line.price_unit
    #             if invoice_line.tax_ids:
    #                 invoice_line_value = invoice_line.tax_ids.with_context(round=False).compute_all(
    #                     adjusted_unit_price, currency=invoice_line.currency_id, quantity=invoice_line.quantity)[
    #                     'total_void']
    #             else:
    #                 invoice_line_value = adjusted_unit_price * invoice_line.quantity
    #             total_invoiced_value += invoice_line.currency_id._convert(
    #                 invoice_line_value, order.currency_id, order.company_id, invoice_line.move_id.invoice_date,
    #                 round=False)
    #             invoiced_qty += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity,
    #                                                                           line.product_id.uom_id)
    #         # TODO currency check
    #         remaining_value = total_invoiced_value - receipt_value
    #         # TODO qty_received in product uom
    #         remaining_qty = invoiced_qty - line.product_uom._compute_quantity(received_qty, line.product_id.uom_id)
    #         if order.currency_id != order.company_id.currency_id and remaining_value and remaining_qty:
    #             # will be rounded during currency conversion
    #             price_unit = remaining_value / remaining_qty
    #         elif remaining_value and remaining_qty:
    #             price_unit = float_round(remaining_value / remaining_qty, precision_digits=price_unit_prec)
    #         else:
    #             price_unit = line._get_gross_price_unit()
    #     else:
    #         price_unit = line._get_gross_price_unit()
    #     if order.currency_id != order.company_id.currency_id:
    #         # The date must be today, and not the date of the move since the move move is still
    #         # in assigned state. However, the move date is the scheduled date until move is
    #         # done, then date of actual move processing. See:
    #         # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
    #         price_unit = price_unit * order.currency_rate
    #         # price_unit = order.currency_id._convert(
    #         #     price_unit, order.company_id.currency_id, order.company_id, date, round=False)
    #     return price_unit
    #
    #
    # def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
    #                                    credit_account_id, svl_id, description):
    #     """ Overridden from stock_account to support amount_currency on valuation lines generated from po
    #     """
    #     self.ensure_one()
    #
    #     rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value,
    #                                                                  debit_account_id, credit_account_id, svl_id,
    #                                                                  description)
    #     purchase_currency = self.purchase_line_id.currency_id
    #     company_currency = self.company_id.currency_id
    #     purchase_currency_rate = self.purchase_line_id.order_id.currency_rate
    #     if not self.purchase_line_id or purchase_currency == company_currency:
    #         return rslt
    #     svl = self.env['stock.valuation.layer'].browse(svl_id)
    #     date = self.env.context.get('force_period_date') if self.env.context.get('force_period_date') else self.date
    #     if not svl.account_move_line_id:
    #         rslt['credit_line_vals']['amount_currency'] = rslt['credit_line_vals']['balance'] / purchase_currency_rate #company_currency._convert(
    #         #     rslt['credit_line_vals']['balance'],
    #         #     purchase_currency,
    #         #     self.company_id,
    #         #     date
    #         # )
    #         rslt['debit_line_vals']['amount_currency'] = rslt['debit_line_vals']['balance'] /  purchase_currency_rate # company_currency._convert(
    #         #     rslt['debit_line_vals']['balance'],
    #         #     purchase_currency,
    #         #     self.company_id,
    #         #     date
    #         # )
    #         rslt['debit_line_vals']['currency_id'] = purchase_currency.id
    #         rslt['credit_line_vals']['currency_id'] = purchase_currency.id
    #
    #     return rslt