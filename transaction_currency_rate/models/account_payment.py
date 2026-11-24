from odoo import api, fields, models, Command, _

from odoo.exceptions import UserError, ValidationError



class AccountPayment(models.Model):
    _inherit = "account.payment"

    currency_rate = fields.Float(
        compute='_compute_currency_rate', inverse='_inverse_currency_rate',digits=(12, 7),
        help="Currency rate from company currency to document currency.",store=True, readonly=False,
    )

    is_multiple_currency = fields.Boolean(
        string="Is currency_id different from the company_currency_id",
        compute='_compute_is_multiple_currency',
    )

    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_is_multiple_currency(self):
        for payment in self:
            payment.is_multiple_currency = payment.currency_id != payment.company_currency_id


    @api.depends('journal_id.currency_id')
    def _compute_currency_rate(self):
        for payment in self:
        
            if payment.currency_id :
                payment.currency_rate = 1 / self.env['res.currency']._get_conversion_rate(
                    from_currency=payment.company_currency_id,
                    to_currency=payment.currency_id,
                    company=payment.company_id,
                    date=payment.date,
                )
            else:
                payment.currency_rate = 1

    def _inverse_currency_rate(self):
        pass

    @api.model
    def _get_trigger_fields_to_synchronize(self):
        fields = super()._get_trigger_fields_to_synchronize()
        return fields + ('currency_rate',)

    def _generate_move_vals(self, write_off_line_vals=None, force_balance=None, line_ids=None):
        values = super()._generate_move_vals(write_off_line_vals, force_balance, line_ids)
        values.update({'currency_rate': self.currency_rate})
        return values

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        res = super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals,
                                                             force_balance=force_balance)

        if self.currency_rate != 1:
            # Compute amounts.
            write_off_line_vals_list = write_off_line_vals or []
            write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
            write_off_balance = sum(x['amount_currency'] * self.currency_rate for x in write_off_line_vals_list)

            withholding_lines = self._prepare_move_withholding_lines({})
            withholding_amount_currency = sum(x['amount_currency'] for x in withholding_lines)
            withholding_balance = sum(x['balance'] for x in withholding_lines)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
            else:
                liquidity_amount_currency = 0.0

            if not write_off_line_vals and force_balance is not None:
                sign = 1 if liquidity_amount_currency > 0 else -1
                liquidity_balance = sign * abs(force_balance)
            else:
                liquidity_balance = liquidity_amount_currency * self.currency_rate

            liquidity_amount_currency -= withholding_amount_currency
            liquidity_balance -= withholding_balance

            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency - withholding_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance - withholding_balance

            res[0].update({
                'amount_currency': liquidity_amount_currency,
                'balance':liquidity_balance
            })
            res[1].update({
                'amount_currency': counterpart_amount_currency,
                'balance': counterpart_balance,

            })
            if write_off_line_vals:
                res[2].update({
                    'balance': write_off_balance
                })
        return res

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    currency_rate = fields.Float(
        compute='_compute_currency_rate', inverse='_inverse_currency_rate',
        help="Currency rate from company currency to document currency.", store=True, readonly=False,
    )

    is_multiple_currency = fields.Boolean(
        string="Is currency_id different from the company_currency_id",
        compute='_compute_is_multiple_currency',
    )


    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_is_multiple_currency(self):
        for payment in self:
            payment.is_multiple_currency = payment.currency_id != payment.company_currency_id


    @api.depends('journal_id.currency_id')
    def _compute_currency_rate(self):
        for move in self:
            if move.currency_id:
                move.currency_rate = 1 / self.env['res.currency']._get_conversion_rate(
                    from_currency=move.company_currency_id,
                    to_currency=move.currency_id,
                    company=move.company_id,
                    date=move.payment_date,
                )
            else:
                move.currency_rate = 1

    def _inverse_currency_rate(self):
        pass

    def _create_payment_vals_from_wizard(self, batch_result):
        """The method that allowed to add the analytic account to the invoice lines
        has been dropped in v13. Fortunately we can add it easily with this
        prepare method.
        """
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals.update({"currency_rate": self.currency_rate})
        return payment_vals

