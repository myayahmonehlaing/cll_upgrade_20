# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _, Command
from odoo.exceptions import UserError
from itertools import chain
from odoo.tools import (
    format_list,
    SQL,
)


class AccountMove(models.Model):
    _inherit = 'account.move'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
        ('none', 'None'),
    ], string='Payment Type', store=True,compute='_compute_payment_type' )

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix

    @api.depends('origin_payment_id','cashbook_id')
    def _compute_payment_type(self):
        for record in self:
            payment_type='none'
            if record.origin_payment_id:
                payment_type = record.origin_payment_id.payment_type
            elif record.cashbook_id:
                payment_type = record.cashbook_id.payment_type

            record.payment_type = payment_type


    def _get_last_sequence_domain(self, relaxed=False):
        condition = super()._get_last_sequence_domain(relaxed)
        if self.facility_id:
            condition =  SQL("%s AND facility_id = %s", condition, self.facility_id.id)
        return condition


    def _get_starting_sequence(self):
        sequence = super()._get_starting_sequence()
        if self.facility_id:
            return self.facility_id.code + "/" + sequence
        return sequence


    def _auto_create_asset(self):
        assets = super()._auto_create_asset()
        for move in self:
            if move.facility_id:
                assets.write(
                    {'facility_id': move.facility_id.id,
                     })


    def _generate_deferred_entries(self):
        """
        Generates the deferred entries for the invoice.
        """
        self.ensure_one()
        if self.state != 'posted':
            return

        for deferred_type in ('expense', 'revenue'):
            moves_vals_to_create = []
            lines_vals_to_create = []
            lines_periods = []
            lines = self.line_ids.filtered(lambda l: (
                l.account_id.internal_group == ('expense' if deferred_type == 'expense' else 'income')
                and l.deferred_start_date
                and l.deferred_end_date
            ))
            if not lines:
                continue

            company_deferred_account = self.company_id.deferred_expense_account_id if deferred_type == "expense" else self.company_id.deferred_revenue_account_id
            deferred_journal = self.company_id.deferred_expense_journal_id if deferred_type == "expense" else self.company_id.deferred_revenue_journal_id
            deferred_method = self.company_id.deferred_expense_amount_computation_method if deferred_type == "expense" else self.company_id.deferred_revenue_amount_computation_method
            if not deferred_journal:
                raise UserError(_("Please set the deferred journal in the accounting settings."))

            facility = self.facility_id.id if self.facility_id else False
            for line in lines:
                periods = line._get_deferred_periods()
                if not periods:
                    continue

                start_date = line.deferred_start_date
                end_date = line.deferred_end_date
                accounting_date = line.date

                # When using the 'full_months' computation method, every consumed month counts as a full month.
                # We therefore need to subtract one month from the end date for the following check on dates.
                if deferred_method == 'full_months':
                    # We need to add one day to the end date since it's excluded by _get_deferred_diff_dates().
                    if self._get_deferred_diff_dates(start_date.replace(day=1), end_date + relativedelta(days=1)) < 2:
                        end_date += relativedelta(months=-1)

                # When all move line dates (start, end, accounting) are within the same month, we skip the line.
                # It would otherwise lead to the creation of both a reversal and a deferral move that would cancel each other out.
                if start_date.replace(day=1) == end_date.replace(day=1) == accounting_date.replace(day=1):
                    continue

                ref = _("Deferral of %s", line.move_id.name or '')

                # Use the deferred account set on the related account if any, otherwise fall back on the company one.
                deferred_account = line.account_id.deferred_account_id or company_deferred_account
                if not deferred_account:
                    raise UserError(_("Please set a deferred account on the related account or in the accounting settings."))

                moves_vals_to_create.append({
                    'move_type': 'entry',
                    'deferred_original_move_ids': [Command.set(line.move_id.ids)],
                    'journal_id': deferred_journal.id,
                    'company_id': self.company_id.id,
                    'partner_id': line.partner_id.id,
                    'auto_post': 'at_date',
                    'ref': ref,
                    'name': False,
                    'date': line.move_id.date,
                    'facility_id': facility,
                })
                lines_vals_to_create.append([
                    {
                        **self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * line.balance, ref, line.analytic_distribution, line),
                        'partner_id': line.partner_id.id,
                        'reconciled_lines_ids': line.ids if not line.reconciled and line.account_id == account else None,
                    }
                    for (account, coeff) in [(line.account_id, -1), (deferred_account, 1)]
                ])
                lines_periods.append((line, periods))
            # create the deferred moves
            moves_fully_deferred = self.create(moves_vals_to_create)
            # We write the lines after creation, to make sure the `deferred_original_move_ids` is set.
            # This way we can avoid adding taxes for deferred moves.
            for move_fully_deferred, lines_vals in zip(moves_fully_deferred, lines_vals_to_create):
                for line_vals in lines_vals:
                    # This will link the moves to the lines. Instead of move.write('line_ids': lines_ids)
                    line_vals['move_id'] = move_fully_deferred.id
            self.env['account.move.line'].create(list(chain(*lines_vals_to_create)))

            deferral_moves_vals = []
            deferral_moves_line_vals = []
            # Create the deferred entries for the periods [deferred_start_date, deferred_end_date]
            for (line, periods), move_vals in zip(lines_periods, moves_vals_to_create):
                deferred_account = line.account_id.deferred_account_id or company_deferred_account
                remaining_balance = line.balance
                for period_index, period in enumerate(periods):
                    # For the last deferral move the balance is forced to remaining balance to avoid rounding errors
                    force_balance = remaining_balance if period_index == len(periods) - 1 else None
                    deferred_amounts = self._get_deferred_amounts_by_line(line, [period], deferred_type)[0]
                    balance = deferred_amounts[period] if force_balance is None else force_balance
                    remaining_balance -= line.currency_id.round(balance)
                    deferral_moves_vals.append({**move_vals, 'date': period[1]})
                    deferral_moves_line_vals.append([
                        {
                            **self.env['account.move.line']._get_deferred_lines_values(account.id, coeff * balance, move_vals['ref'], line.analytic_distribution, line),
                            'partner_id': line.partner_id.id,
                            'product_id': line.product_id.id,
                        }
                        for (account, coeff) in [(deferred_amounts['account_id'], 1), (deferred_account, -1)]
                    ])

            deferral_moves = self.create(deferral_moves_vals)
            for deferral_move, lines_vals in zip(deferral_moves, deferral_moves_line_vals):
                for line_vals in lines_vals:
                    # This will link the moves to the lines. Instead of move.write('line_ids': lines_ids)
                    line_vals['move_id'] = deferral_move.id
            self.env['account.move.line'].create(list(chain(*deferral_moves_line_vals)))

            # Avoid having deferral moves with a total amount of 0.
            to_unlink = deferral_moves.filtered(lambda move: move.currency_id.is_zero(move.amount_total))
            to_unlink.unlink()

            (moves_fully_deferred + deferral_moves - to_unlink)._post(soft=True)



    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        move_vals = super()._prepare_move_for_asset_depreciation(vals)
        asset = vals['asset_id']
        if asset.facility_id:
            move_vals['facility_id'] = asset.facility_id.id
        return move_vals

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('facility'):
            for vals in vals_list:
                vals['facility_id'] = self.env.context.get('facility')
        return super().create(vals_list)

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )
    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix