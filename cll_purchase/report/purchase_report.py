# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#

from odoo import fields, models, api
from odoo.tools.sql import SQL

class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    purchase_currency_id =  fields.Many2one("res.currency",readonly=True,string="Purchase Currency")
    currency_total = fields.Monetary(string='Currency Total', currency_field='purchase_currency_id', readonly=True)

    def _select(self):
        return SQL(
            "%s, po.currency_id  as  purchase_currency_id, "
            " sum(l.price_subtotal) as currency_total",
            super()._select(),
        )

    def _group_by(self):
        return SQL(
            "%s, po.currency_id",
            super()._group_by(),
        )


