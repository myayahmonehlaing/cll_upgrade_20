# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Please note that these reports are not multi-currency !!!
#

from odoo import fields, models, api
from odoo.models import TableSQL
from odoo.tools.sql import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    def _select_list(self, table: TableSQL):
        res = super()._select_list(table)

        uom_ratio = SQL(
            "(COALESCE(%s, 1) / NULLIF(COALESCE(%s, 1), 0.0))",
            table.uom_id.factor,
            table.product_id.uom_id.factor,
        )

        replacements = {
            'price_total': SQL(
                "SUM(%s * COALESCE(%s, 1.0))::decimal(16,2) * %s as price_total",
                table.price_total, table.order_id.currency_rate, table.consolidation_rate,
            ),
            'price_average': SQL(
                "(SUM(%s * %s * COALESCE(%s, 1.0))/NULLIF(SUM(%s * %s),0.0))::decimal(16,2) * %s as price_average",
                table.product_qty, table.price_unit, table.order_id.currency_rate,
                table.product_qty, uom_ratio, table.consolidation_rate,
            ),
            'untaxed_total': SQL(
                "SUM(%s * COALESCE(%s, 1.0))::decimal(16,2) * %s as untaxed_total",
                table.price_subtotal, table.order_id.currency_rate, table.consolidation_rate,
            ),
        }

        def _alias_of(field):
            # Extract the trailing alias from the SQL template (e.g. "... AS price_total")
            if not isinstance(field, SQL):
                return None
            # SQL objects expose their query via .code or similar depending on Odoo version.
            # Fallback to str() which is safe for matching.
            text = str(field).lower()
            for alias in replacements:
                if f"as {alias}" in text:
                    return alias
            return None

        result = []
        for field in res:
            alias = _alias_of(field)
            if alias and alias in replacements:
                result.append(replacements[alias])
            else:
                result.append(field)
        return result


