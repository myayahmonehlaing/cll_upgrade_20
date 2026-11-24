"""Extensions to Account Move and Account Move Line Models."""

# pylint: disable=import-error,too-few-public-methods,protected-access,too-many-positional-arguments,too-many-locals,unused-argument,too-many-arguments
from odoo import Command, _, api, fields, models
from odoo.tools import frozendict
from collections import defaultdict
from ..dataclasses.datamodels import InvoiceStatus


class AccountMove(models.Model):
    """Extensions to Account Move Model."""

    _inherit = "account.move"

    ehr_invoice_status = fields.Selection(
        selection=InvoiceStatus.get_selection(), string="EHR Invoice Status", store=True
    )
    partner_group_id = fields.Many2one("res.partner.group", string="Patient Category")
    refer_id = fields.Many2one(comodel_name="res.partner", string="Refer Doctor")

class AccountMoveLine(models.Model):
    """Extensions to Account Move Line Model."""

    _inherit = "account.move.line"

    discount_amount = fields.Float("Discount Amt.")

    refer_id = fields.Many2one(comodel_name="res.partner", string="Refer Doctor")

    @api.depends('quantity', 'discount', 'discount_amount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        super()._compute_totals()

    @api.depends('account_id', 'company_id', 'discount', 'price_unit', 'quantity', 'currency_rate',
                 'analytic_distribution')
    def _compute_discount_allocation_needed(self):
        line2discounted_amount = {
            line: [
                (line.account_id, amount_currency,
                 line.company_currency_id.round(amount_currency / line.currency_rate)),
                (discount_allocation_account, -amount_currency,
                 -line.company_currency_id.round(amount_currency / line.currency_rate)),
            ]
            for line in self.move_id.line_ids
            if line.display_type == 'product'
               and (discount_allocation_account := line.move_id._get_discount_allocation_account())
               and line.account_id != discount_allocation_account
               and (amount_currency := line.currency_id.round(
                line.move_id.direction_sign * ( line.quantity * line.price_unit * line.discount / 100 ) - line.discount_amount
            ))
        }

        distribution_totals = defaultdict(lambda: defaultdict(float))
        for line, discounted_amounts in line2discounted_amount.items():
            for account, _amount_currency, amount in discounted_amounts:
                for analytic_account_id in line.analytic_distribution or {}:
                    distribution_totals[frozendict({
                        'move_id': line.move_id.id,
                        'account_id': account.id,
                        'currency_rate': line.currency_rate,
                    })][analytic_account_id] += amount

        for line in self:
            line.discount_allocation_dirty = True
            if line not in line2discounted_amount:
                line.discount_allocation_needed = False
                continue

            discount_allocation_needed = {}
            for account, amount_currency, amount in line2discounted_amount[line]:
                key = frozendict({
                    'move_id': line.move_id.id,
                    'account_id': account.id,
                    'currency_rate': line.currency_rate,
                })
                dist = distribution_totals[key]
                total = sum(dist.values()) or 1  # avoid division by zero
                discount_allocation_needed[key] = frozendict({
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': amount_currency,
                    'balance': amount,
                    'analytic_distribution': {
                        account_id: 100 * value / total
                        for account_id, value in dist.items()
                    }
                })
            line.discount_allocation_needed = discount_allocation_needed

class AccountTax(models.Model):
    """Extensions to Account Tax Model."""

    _inherit = "account.tax"

    @api.model
    def _prepare_base_line_for_taxes_computation(self, record, **kwargs):
        base_line = super()._prepare_base_line_for_taxes_computation(record, **kwargs)

        def load(field, fallback):
            return self._get_base_line_field_value_from_record(record, field, kwargs, fallback)
        base_line['discount_amount'] = load('discount_amount', 0.0) or load('ehr_discount', 0.0)
        return base_line

    @api.model
    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
        """ Perform the taxes computation for the base line and add it to the base line under
        the 'tax_details' key. Those values are rounded or not depending of the tax calculation method.
        If you need to compute monetary fields with that, you probably need to call
        '_round_base_lines_tax_details' after this method.

        The added tax_details is a dictionary containing:
        raw_total_excluded_currency:    The total without tax expressed in foreign currency.
        raw_total_excluded:             The total without tax expressed in local currency.
        raw_total_included_currency:    The total tax included expressed in foreign currency.
        raw_total_included:             The total tax included expressed in local currency.
        taxes_data:                     A list of python dictionary containing the taxes_data returned by '_get_tax_details' but
                                        with the amounts expressed in both currencies:
            raw_tax_amount_currency         The tax amount expressed in foreign currency.
            raw_tax_amount                  The tax amount expressed in local currency.
            raw_base_amount_currency        The tax base amount expressed in foreign currency.
            raw_base_amount                 The tax base amount expressed in local currency.

        [!] Mirror of the same method in account_tax.js.
        PLZ KEEP BOTH METHODS CONSISTENT WITH EACH OTHERS.

        :param base_line:       A base line generated by '_prepare_base_line_for_taxes_computation'.
        :param company:         The company owning the base line.
        :param rounding_method: The rounding method to be used. If not specified, it will be taken from the company.
        """
        rounding_method = rounding_method or company.tax_calculation_rounding_method
        price_unit_after_discount = base_line['price_unit'] * (1 - (base_line['discount'] / 100.0))

        discounted_amount_price_unit = (
            (price_unit_after_discount * base_line['quantity'] - base_line['discount_amount']) / base_line['quantity']
            if  base_line['quantity'] else price_unit_after_discount
        )

        taxes_computation = base_line['tax_ids']._get_tax_details(
            price_unit=discounted_amount_price_unit,
            quantity=base_line['quantity'],
            precision_rounding=base_line['currency_id'].rounding,
            rounding_method=rounding_method,
            product=base_line['product_id'],
            product_uom=base_line['product_uom_id'],
            special_mode=base_line['special_mode'],
            filter_tax_function=base_line['filter_tax_function'],
        )

        # Only python side for professional with reverse charge
        if base_line['special_type'] == 'non_deductible':
            taxes_data = taxes_computation['taxes_data']
            taxes_computation['taxes_data'] = []
            for tax_data in taxes_data:
                if not tax_data.get('is_reverse_charge'):
                    taxes_computation['taxes_data'].append(tax_data)
                else:
                    taxes_computation['total_included'] -= tax_data['tax_amount']

        rate = base_line['rate']
        tax_details = base_line['tax_details'] = {
            'raw_total_excluded_currency': taxes_computation['total_excluded'],
            'raw_total_excluded': taxes_computation['total_excluded'] / rate if rate else 0.0,
            'raw_total_included_currency': taxes_computation['total_included'],
            'raw_total_included': taxes_computation['total_included'] / rate if rate else 0.0,
            'taxes_data': [],
        }
        if rounding_method == 'round_per_line':
            tax_details['raw_total_excluded'] = company.currency_id.round(tax_details['raw_total_excluded'])
            tax_details['raw_total_included'] = company.currency_id.round(tax_details['raw_total_included'])
        for tax_data in taxes_computation['taxes_data']:
            tax_amount = tax_data['tax_amount'] / rate if rate else 0.0
            base_amount = tax_data['base_amount'] / rate if rate else 0.0
            if rounding_method == 'round_per_line':
                tax_amount = company.currency_id.round(tax_amount)
                base_amount = company.currency_id.round(base_amount)
            tax_details['taxes_data'].append({
                **tax_data,
                'raw_tax_amount_currency': tax_data['tax_amount'],
                'raw_tax_amount': tax_amount,
                'raw_base_amount_currency': tax_data['base_amount'],
                'raw_base_amount': base_amount,
            })

    def _prepare_base_line_grouping_key(self, base_line):
        results = super()._prepare_base_line_grouping_key(base_line)
        results['discount_amount'] = base_line['discount_amount']

        return results
