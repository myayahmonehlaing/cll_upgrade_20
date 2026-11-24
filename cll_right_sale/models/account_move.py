# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command, SUPERUSER_ID, modules, tools
from odoo.tools import frozendict

class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        'invoice_payment_term_id',
        'invoice_date',
        'currency_id',
        'amount_total_in_currency_signed',
        'invoice_date_due',
    )
    def _compute_needed_terms(self):
        super()._compute_needed_terms()
        SaleCenter = self.env['sale.center'].sudo()
        for invoice in self:
            sale_order = invoice.line_ids.sale_line_ids.order_id
            if not (
                    invoice.company_id.right_sale
                    and len(sale_order) == 1
            ):
                continue

            center = SaleCenter.search(
                [('warehouse_id', '=', sale_order.warehouse_id.id)],
                limit=1,
            )
            if not center.analytic_account_id:
                continue

            distribution = {center.analytic_account_id.id: 100}
            invoice.needed_terms = {
                frozendict({**key, 'analytic_distribution': distribution}): value
                for key, value in invoice.needed_terms.items()
            }


    def _reconcile_reversed_moves(self, reverse_moves, move_reverse_cancel):
        ''' Reconciles moves in self and reverse moves
        :param move_reverse_cancel: parameter used when lines are reconciled
                                    will determine whether the tax cash basis journal entries should be created
        :param reverse_moves:       An account.move recordset, reverse of the current self.
        :return:                    An account.move recordset, reverse of the current self.
        '''
        for move, reverse_move in zip(self, reverse_moves):
            group = (move.line_ids + reverse_move.line_ids) \
                .filtered(lambda l: not l.reconciled) \
                .grouped(lambda l: (l.account_id, l.currency_id))
            for (account, _currency), lines in group.items():
                if (account.reconcile and not account.account_type == 'liability_current' ) or account.account_type in ('asset_cash', 'liability_credit_card'):
                    lines.with_context(move_reverse_cancel=move_reverse_cancel).reconcile()
        return reverse_moves

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _reconcile_plan_with_sync(self, plan_list, all_amls):
        super()._reconcile_plan_with_sync(plan_list, all_amls)
        analytic_line = self.filtered(lambda l: l.analytic_distribution != False and l.account_type =='asset_receivable')
        if analytic_line:
            no_analytic_line = self - analytic_line
            no_analytic_line.write({'analytic_distribution': analytic_line[0].analytic_distribution})





