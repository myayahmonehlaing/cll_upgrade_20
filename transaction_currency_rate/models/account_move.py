from contextlib import contextmanager
from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    currency_rate = fields.Float(
        compute='_compute_currency_rate', inverse='_inverse_currency_rate',precompute=True,
        string="Custom Currency rate", help="Currency rate from company currency to document currency.",
        store=True, readonly=False,
    )

    is_multiple_currency = fields.Boolean(
        string="Is currency_id different from the company_currency_id",
        compute='_compute_is_multiple_currency',
    )

    @api.depends('currency_id')
    def _compute_currency_rate(self):
        for move in self:
            if move.currency_id :
                move.currency_rate = 1 / self.env['res.currency']._get_conversion_rate(
                    from_currency=move.company_currency_id,
                    to_currency=move.currency_id,
                    company=move.company_id,
                    date=move._get_rate_date(),
                )
            else:
                move.currency_rate = 1

    @api.depends('currency_id')
    def _inverse_currency_rate(self):
        self._conditional_add_to_compute('currency_id', lambda m: (
                not m.currency_id
                or m.journal_id.currency_id and m.currency_id != m.journal_id.currency_id
        ))

    def _get_rate_date(self):
        self.ensure_one()
        return self.invoice_date or self.date or fields.Date.context_today(self)

    @api.depends('currency_id','currency_rate','company_currency_id', 'company_id', 'taxable_supply_date')
    def _compute_invoice_currency_rate(self):
        for move in self:
            if move.is_invoice(include_receipts=True):
                move.invoice_currency_rate = 1 /  move.currency_rate


    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_is_multiple_currency(self):
        for move in self:
            move.is_multiple_currency = move.currency_id != move.company_currency_id

    def refresh_invoice_currency_rate(self):
        for move in self:
            move.invoice_currency_rate =  1 /  move.currency_rate


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # currency_rate = fields.Float(
    #     compute='_compute_currency_rate',
    #     help="Currency rate from company currency to document currency.",
    # )
    #
    # @api.depends('currency_id', 'company_id', 'move_id.date','move_id.currency_rate',)
    # def _compute_currency_rate(self):
    #     for line in self:
    #         if line.currency_id :
    #             default_rate = self.env['res.currency']._get_conversion_rate(
    #                 from_currency=line.company_currency_id,
    #                 to_currency=line.currency_id,
    #                 company=line.company_id,
    #                 date=line._get_rate_date(),
    #             )
    #             line.currency_rate = ( 1 /  line.move_id.currency_rate )  if line.move_type != 'entry' else default_rate
    #         else:
    #             line.currency_rate = 1
    #
    #
    # def _check_constrains_account_id_journal_id(self):
    #     # Avoid using api.constrains for fields journal_id and account_id as in case of a write on
    #     # account move and account move line in the same operation, the check would be done
    #     # before all write are complete, causing a false positive
    #     self.flush_recordset()
    #     for line in self.filtered(lambda x: x.display_type not in ('line_section', 'line_note')):
    #         account = line.account_id
    #         journal = line.move_id.journal_id
    #
    #         if account.deprecated and not self.env.context.get('skip_account_deprecation_check'):
    #             raise UserError(_('The account %s (%s) is deprecated.', account.name, account.code))
    #
    #         # account_currency = account.currency_id
    #         # if account_currency and account_currency != line.company_currency_id and account_currency != line.currency_id:
    #         #     raise UserError \
    #         #         (_('The account selected on your journal entry forces to provide a secondary currency. You should remove the secondary currency on the account.'))
    #
    #         if account.allowed_journal_ids and journal not in account.allowed_journal_ids:
    #             raise UserError \
    #                 (_('You cannot use this account (%s) in this journal, check the field \'Allowed Journals\' on the related account.',
    #                    account.display_name))
    #
    #         if account in (journal.default_account_id, journal.suspense_account_id):
    #             continue
    #
    #         is_account_control_ok = not journal.account_control_ids or account in journal.account_control_ids
    #
    #         if not is_account_control_ok:
    #             raise UserError \
    #                 (_("You cannot use this account (%s) in this journal, check the section 'Control-Access' under "
    #                    "tab 'Advanced Settings' on the related journal.", account.display_name))
    #
    # @contextmanager
    # def _sync_invoice(self, container):
    #     if container['records'].env.context.get('skip_invoice_line_sync'):
    #         yield
    #         return  # avoid infinite recursion
    #
    #     def existing():
    #         return {
    #             line: {
    #                 'amount_currency': line.currency_id.round(line.amount_currency),
    #                 'balance': line.company_id.currency_id.round(line.balance),
    #                 'currency_rate': line.currency_rate,
    #                 'price_subtotal': line.currency_id.round(line.price_subtotal),
    #                 'move_type': line.move_id.move_type,
    #             } for line in container['records'].with_context(
    #                 skip_invoice_line_sync=True,
    #             ).filtered(lambda l: l.move_id.is_invoice(True))
    #         }
    #
    #     def changed(fname):
    #         return line not in before or before[line][fname] != after[line][fname]
    #
    #     before = existing()
    #     yield
    #     after = existing()
    #     for line in after:
    #         if (
    #                 line.display_type == 'product'
    #                 and not self.env.is_protected(self._fields['amount_currency'], line)
    #                 and (not changed('amount_currency') or line not in before)
    #         ):
    #             amount_currency = line.move_id.direction_sign * line.currency_id.round(line.price_subtotal)
    #             if line.amount_currency != amount_currency or line not in before:
    #                 line.amount_currency = amount_currency
    #             if line.currency_id == line.company_id.currency_id:
    #                 line.balance = amount_currency
    #
    #     after = existing()
    #     for line in after:
    #         if (
    #                 (changed('amount_currency') or changed('currency_rate') or changed('move_type'))
    #                 # and not self.env.is_protected(self._fields['balance'], line)
    #                 # and (not changed('balance')
    #                 and not line.display_type == 'cogs'
    #                      or (line not in before and not line.balance)
    #         ):
    #             balance = line.company_id.currency_id.round(line.amount_currency / line.currency_rate)
    #             line.balance = balance
    #     # Since this method is called during the sync, inside of `create`/`write`, these fields
    #     # already have been computed and marked as so. But this method should re-trigger it since
    #     # it changes the dependencies.
    #     self.env.add_to_compute(self._fields['debit'], container['records'])
    #     self.env.add_to_compute(self._fields['credit'], container['records'])



