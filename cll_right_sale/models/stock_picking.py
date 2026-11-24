# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):

        res = super().button_validate()
        MoveLine = self.env["account.move.line"].with_context(
            check_move_validity=False, skip_invoice_sync=True)
        for picking in self:
            if picking.sale_id and picking.company_id.right_sale and picking.state =='done' and picking.picking_type_code in ('incoming','outgoing'):
                if not picking.company_id.right_deferred_journal_id:
                    raise ValidationError("Please select a deferred journal before delivery order is done.")

                inv_lines = self.env["account.move.line"]
                reconcile_items = []
                move_type = 'out_invoice' if picking.picking_type_code == 'outgoing' else 'out_refund'

                for inv_line in picking.move_ids.filtered(lambda m: m.quantity != 0.0).mapped(
                    'sale_line_id'):
                    for line in inv_line.invoice_lines.filtered(lambda  m: m.move_type == move_type
                     and m.parent_state == 'posted'  and m.reconciled == False):

                        if line.account_type == 'liability_current':
                            inv_lines += line


                if not inv_lines :
                    raise ValidationError(
                        "To generate a deferred entry, the invoice needs to be opened with deferred account")

                if any(line.parent_state !='posted' for line in inv_lines):
                    raise ValidationError("To generate a deferred entry, the invoice needs to be posted.")

                if inv_lines:
                    account_move = self.env["account.move"].sudo().create(
                        {
                            "journal_id": picking.company_id.right_deferred_journal_id.id,
                            "date": fields.Date.context_today(picking),
                            "ref": picking.sale_id.name,
                        })

                    for line in inv_lines:
                        debit_line = MoveLine.sudo().create({
                            "product_id": line.product_id.id,
                            "account_id": line.account_id.id,
                            "move_id": account_move.id,
                            "analytic_distribution": line.analytic_distribution,
                            "debit": line.credit if move_type == 'out_invoice' else 0.0,
                            "credit": 0.0 if move_type == 'out_invoice' else line.debit,
                        })
                        MoveLine.sudo().create({
                            "product_id": line.product_id.id,
                            "account_id": line.product_id.categ_id.property_account_sale_categ_id.id,
                            "move_id": account_move.id,
                            "analytic_distribution":  line.analytic_distribution,
                            "debit": 0.0 if move_type == 'out_invoice' else line.debit ,
                            "credit": line.credit if move_type == 'out_invoice' else 0.0,
                        })
                        reconcile_items.append(debit_line + line )
                    account_move.sudo().action_post()
                    body = _("A deferred journal entry has been created: ") + account_move._get_html_link()
                    picking.sudo().message_post(body=body,	author_id=self.env.ref('base.partner_root').id)
                [items.filtered(lambda m: m.reconciled ==False).reconcile() for items in reconcile_items]
        return res