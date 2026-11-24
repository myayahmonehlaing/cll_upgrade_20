# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

from odoo.models import TableSQL
from odoo.tools import SQL, clean_context

class SaleReport(models.Model):
    _inherit = "sale.report"

    def _select_dict(self, table: TableSQL):
        order_rate = self._case_value_or_one(table.order_id.currency_rate)
        rate = SQL("%s * %s", table.consolidation_rate, order_rate)
        select_vals = super()._select_dict(table)
        select_vals.update({
            'price_unit': SQL("CASE WHEN %s IS NOT TRUE THEN AVG(%s / %s) ELSE 0 END", table.is_downpayment,
                              table.price_unit, rate),
            'price_total': SQL("CASE WHEN %s IS NOT TRUE THEN SUM(%s / %s) ELSE 0 END", table.is_downpayment,
                               table.price_total, rate),
            'price_subtotal': SQL("CASE WHEN %s IS NOT TRUE THEN SUM(%s / %s) ELSE 0 END", table.is_downpayment,
                                  table.price_subtotal, rate),
            'untaxed_amount_to_invoice': SQL("SUM(%s / %s)", table.untaxed_amount_to_invoice, rate),
            'untaxed_amount_invoiced': SQL("SUM(%s / %s)", table.untaxed_amount_invoiced, rate),
            'untaxed_delivered_amount': SQL("SUM(%s * %s / %s)", table.price_unit, table.qty_delivered, rate),
        })
        return select_vals

