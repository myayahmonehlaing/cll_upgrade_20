# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning



class AccountCashbook(models.Model):
    _name = "account.cashbook"
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']
    _description = "Cashbook"
    _order = "date desc, name desc"
    _check_company_auto = True

    name = fields.Char(string="Number", compute='_compute_name', store=True)
    date = fields.Date(default=fields.Date.context_today, required=True, tracking=True)
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        index=True,
        copy=False,
        check_company=True)
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        compute='_compute_journal_id', store=True, readonly=False, precompute=True,
        check_company=True,
        index=False,  # covered by account_payment_journal_id_company_id_idx
        required=True,
    )
    available_cash_bank_account_ids = fields.Many2many(
        comodel_name='account.account',
        compute='_compute_available_cash_bank_account_ids'
    )
    available_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        compute='_compute_available_journal_ids'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        compute='_compute_company_id', store=True, readonly=False, precompute=True,
        index=False,  # covered by account_payment_journal_id_company_id_idx
        required=True
    )
    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('paid', "Paid"),
            ('canceled', "Canceled"),
            ('rejected', "Rejected"),
        ],
        required=True,
        default='draft',
        compute='_compute_state', store=True, readonly=False,
        copy=False,
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        help="The payment's currency.")

    currency_rate = fields.Float(
        compute='_compute_currency_rate', inverse='_inverse_currency_rate',
        help="Currency rate from company currency to document currency.",store=True, readonly=False,
    )


    company_currency_id = fields.Many2one(string="Company Currency", related='company_id.currency_id')

    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True, tracking=True)
    memo = fields.Char(string="Memo", tracking=True)
    amount_total = fields.Monetary(currency_field='currency_id', compute='_compute_amount_total')

    line_ids = fields.One2many(
        'account.cashbook.line',
        'cashbook_id',
        string='Cashbook Lines',
        copy=True,
    )

    cash_bank_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Account",
        index='btree_not_null',
        store=True,
        compute='_compute_cash_bank_account_id',
        check_company=True)



    is_multiple_currency = fields.Boolean(
        string="Is currency_id different from the company_currency_id",
        compute='_compute_is_multiple_currency',
    )
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
        readonly=False, store=True, copy=False,
        compute='_compute_payment_method_line_id',
        domain="[('id', 'in', available_payment_method_line_ids)]",
        help="Manual: Pay or Get paid by any method outside of Odoo.\n"
        "Payment Providers: Each payment provider has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
        "Check: Pay bills by check and print it from Odoo.\n"
        "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
        "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
        "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line',
        compute='_compute_payment_method_line_fields')

    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_is_multiple_currency(self):
        for payment in self:
            payment.is_multiple_currency = payment.currency_id != payment.company_id.currency_id

    @api.depends('currency_id')
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

    @api.depends('currency_id')
    def _inverse_currency_rate(self):
        pass

    @api.depends('journal_id', 'payment_type',)
    def _compute_cash_bank_account_id(self):
        self.ensure_one()
        for payment in self:
            payment.cash_bank_account_id = payment.payment_method_line_id.payment_account_id


    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
        '''
        for payment in self:
            available_payment_method_lines = payment.available_payment_method_line_ids

            # Select the first available one by default.
            if payment.payment_method_line_id in available_payment_method_lines:
                payment.payment_method_line_id = payment.payment_method_line_id
            elif available_payment_method_lines:
                payment.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                payment.payment_method_line_id = False

    @api.depends('payment_type')
    def _compute_available_journal_ids(self):
        """
        Get all journals having at least one payment method for inbound/outbound depending on the payment_type.
        """
        journals = self.env['account.journal'].search([
            '|',
            ('company_id', 'parent_of', self.env.company.id),
            ('company_id', 'child_of', self.env.company.id),
            ('type', 'in', ('bank', 'cash', 'credit')),
        ])
        for payment in self:
            if payment.payment_type == 'inbound':
                payment.available_journal_ids = journals.filtered('inbound_payment_method_line_ids')
            else:
                payment.available_journal_ids = journals.filtered('outbound_payment_method_line_ids')


    @api.depends('payment_type')
    def _compute_available_cash_bank_account_ids(self):
        """
        Get all journals having at least one payment method for inbound/outbound depending on the payment_type.
        """
        for payment in self:
            payment.available_cash_bank_account_ids = self.env['account.account'].search([
            '|',
            ('company_id', 'parent_of', self.env.company.id),
            ('company_id', 'child_of', self.env.company.id),
            ('account_type', '=', 'asset_cash'),
        ])

    def _get_payment_method_codes_to_exclude(self):
        # can be overriden to exclude payment methods based on the payment characteristics
        self.ensure_one()
        return []


    @api.depends('payment_type', 'journal_id', 'currency_id')
    def _compute_payment_method_line_fields(self):
        for payment in self:
            payment.available_payment_method_line_ids = payment.journal_id._get_available_payment_method_lines(payment.payment_type)
            to_exclude = payment._get_payment_method_codes_to_exclude()
            if to_exclude:
                payment.available_payment_method_line_ids = payment.available_payment_method_line_ids.filtered(lambda x: x.code not in to_exclude)



    @api.depends('state')
    def _compute_name(self):
        for payment in self:
            if payment and payment.state in ('paid'):
                payment.name =  (  payment.move_id.name  or
                    self.env['ir.sequence'].with_company(payment.company_id).next_by_code(
                        'account.cashbook',
                        sequence_date=payment.date,
                    )
                )


    @api.depends('company_id')
    def _compute_journal_id(self):
        for payment in self:
            company = self.company_id or self.env.company
            payment.journal_id = self.env['account.journal'].search([
                *self.env['account.journal']._check_company_domain(company),
                ('type', 'in', ['bank', 'cash', 'credit']),
            ], limit=1)

    @api.depends('journal_id')
    def _compute_company_id(self):
        for payment in self:
            if payment.journal_id.company_id not in payment.company_id.parent_ids:
                payment.company_id = (payment.journal_id.company_id or self.env.company)._accessible_branches()[:1]


    @api.depends('journal_id')
    def _compute_currency_id(self):
        for payment in self:
            payment.currency_id = payment.journal_id.currency_id or payment.journal_id.company_id.currency_id

    @api.depends('line_ids.amount')
    def _compute_amount_total(self):
        for payment in self:
            payment.amount_total =  sum(payment.line_ids.mapped('amount'))

    def write(self, vals):

        if vals.get('state') == 'paid' and not vals.get('move_id'):

            self.filtered(lambda p: not p.move_id)._generate_journal_entry()
            self.move_id.action_post()
        res = super().write(vals)
        return res

    def _prepare_move(self, force_balance=None, line_ids=None):

        return {
            'move_type': 'entry',
            'ref': self.memo,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': line_ids or [
                Command.create(line_vals)
                for line_vals in self._prepare_move_line_default_vals(
                    force_balance=force_balance,

                )
            ],
            'cashbook_id': self.id,
            'currency_rate': self.currency_rate,
        }


    def _generate_journal_entry(self):
        need_move = self.filtered(lambda p: not p.move_id)
        move_vals = []
        for payment in need_move:
            move_vals.append(payment._prepare_move())

        moves = self.env['account.move'].create(move_vals)
        for payment, move in zip(need_move, moves):
            payment.write({'move_id': move.id, 'state': 'paid'})




    def _prepare_move_line_default_vals(self,force_balance=None):

        self.ensure_one()

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount_total
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount_total
        else:
            liquidity_amount_currency = 0.0

        if  force_balance is not None:
            sign = 1 if liquidity_amount_currency > 0 else -1
            liquidity_balance = sign * abs(force_balance)
        else:
            liquidity_balance = liquidity_amount_currency * self.currency_rate
            # liquidity_balance = self.currency_id._convert(
            #     liquidity_amount_currency,
            #     self.company_id.currency_id,
            #     self.company_id,
            #     self.date,
            # )


        currency_id = self.currency_id.id

        # Compute a default label to set on the journal items.
        liquidity_line_name = self.memo


        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                # 'partner_id': self.partner_id.id,
                'account_id': self.cash_bank_account_id.id,

            },

        ]

        for line in self.line_ids:
            counterpart_amount_currency =  line.amount * ( - 1 if liquidity_amount_currency > 0 else 1 )
            counterpart_balance = counterpart_amount_currency * line.cashbook_id.currency_rate
            # counterpart_balance = line.currency_id._convert(
            #     counterpart_amount_currency,
            #     line.cashbook_id.company_id.currency_id,
            #     line.cashbook_id.company_id,
            #     line.cashbook_id.date,
            # )
            line_vals_list.append(
                {
                    'name': line.name,
                    'date_maturity': line.cashbook_id.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': - counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    # 'partner_id': self.partner_id.id,
                    'account_id': line.account_id.id,
                    'analytic_distribution':line.analytic_distribution
                },
            )

        return line_vals_list

    def action_post(self):
        ''' draft -> posted '''
        # Do not allow posting if the account is required but not trusted

        self.state = 'paid'

    # def action_validate(self):
    #     self.state = 'paid'
    def action_draft(self):
        self.state = 'draft'
        self.move_id.filtered(lambda m: m.state != 'draft').button_draft()
        self.move_id.unlink()


    def button_open_journal_entry(self):
        ''' Redirect the user to this payment journal.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }

    def unlink(self):
        for payment in self:
            if payment.state != "draft":
                raise UserError(
                    _("The %s is not in draft state, so you cannot delete it.")
                    % payment.name
                )
        return super().unlink()