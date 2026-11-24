# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval

get_hundred_warehouse = lambda w : {key: 100 for key, value in w.items() if value in [80, 100]}

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', compute=None, store=True, copy=False)

    is_transfer = fields.Boolean(string='Transfer?', compute='_compute_is_transfer', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(SaleOrderLine, self).create(vals_list)
        for line in lines:
            if line.company_id.right_sale:
                line.filtered(lambda line: line.product_id.type == 'service').separate_analytic_service()
        return lines

    def write(self, values):
        lines = self.env['sale.order.line'].filtered(lambda r: r.product_id.type == 'service')
        res = super(SaleOrderLine, self).write(values)
        if lines.company_id.right_sale and lines:
            lines.separate_analytic_service()
        return res

    @api.depends('warehouse_id', 'order_id.warehouse_id')
    def _compute_is_transfer(self):
        for record in self:
            record.is_transfer = True if record.company_id.right_sale and record.warehouse_id and (record.warehouse_id != record.order_id.warehouse_id) else False

    def _get_center_line_domain(self, center_id: int, product_id: int) -> tuple[list]:
        return [
            ('center_id', '=', center_id),
            ('product_id', '=', product_id)
        ]

    def _get_center_domain(self, warehouse_id: int) -> tuple[list]:
        return [
            ('warehouse_id', '=', warehouse_id)
        ]

    def get_center_line(self, domain)-> models.Model:
        return self.env['sale.center.product.line'].sudo().search(domain, order='create_date DESC', limit=1)

    def get_analytic_by_warehouse_id(self, domain)-> models.Model:
        return self.env['sale.center'].sudo().search(domain, order='create_date DESC', limit=1)

    def _get_warehouse_and_centers(self):
        """Retrieve warehouse and center-related IDs."""
        warehouse_id = self.order_id.warehouse_id
        center_id = self._get_analytic_center(warehouse_id.id)
        center_line_id = self.get_center_line(
            domain=self._get_center_line_domain(center_id=center_id.id, product_id=self.product_id.id)
        )
        if self.warehouse_id:
            warehouse_id=self.warehouse_id
        elif center_line_id:
            warehouse_id = center_line_id.warehouse_id
        transfer_center_id = self._get_analytic_center(warehouse_id.id)

        return warehouse_id, center_line_id, center_id, transfer_center_id

    def _update_warehouse_and_compute_transfer(self, warehouse_id):
        """Update warehouse and compute transfer flag."""
        if not self.warehouse_id:
            self.with_user(SUPERUSER_ID).write({'warehouse_id': warehouse_id})
        self._compute_is_transfer()

    def _get_analytic_center(self, warehouse_id):
        """Get analytic center for the given warehouse."""
        return self.get_analytic_by_warehouse_id(
            domain=self._get_center_domain(warehouse_id=warehouse_id)
        )

    def _calculate_analytic_distribution(self, center_id, transfer_center_id):
        """Calculate analytic distribution based on transfer status."""
        distribution = defaultdict(dict)

        sales_analytic_distribution = literal_eval(
            self.env['ir.config_parameter'].sudo().get_str('sales_analytic_distribution')
        )
        if sales_analytic_distribution.get(str(self.company_id.id)) == 100:
            if self.is_transfer and transfer_center_id:
                return (
                    {str(center_id.analytic_account_id.id): 100},
                    {str(transfer_center_id.analytic_account_id.id): 100},
                )
            return (
                {str(center_id.analytic_account_id.id): 100},
                {str(center_id.analytic_account_id.id): 100},
            )

        if not center_id:
            return distribution, distribution

        if self.is_transfer and transfer_center_id:
            distribution[str(center_id.analytic_account_id.id)] = 20
            distribution[str(transfer_center_id.analytic_account_id.id)] = 80
        else:
            distribution[str(center_id.analytic_account_id.id)] = 100

        return distribution, distribution


    def _format_analytic_distribution(self, distribution):
        """Format analytic distribution for procurement."""
        return get_hundred_warehouse(distribution)

    def _update_analytic_value(self, analytic_distribution_value):
        return self.with_user(SUPERUSER_ID).write({
            'analytic_distribution': analytic_distribution_value
        })

    def _get_analytic_value(self, center_id, transfer_center_id):
        analytic_distribution_value = self._calculate_analytic_distribution(center_id, transfer_center_id)
        # Update fields with a single write
        self.with_user(SUPERUSER_ID).write({
            'analytic_distribution': analytic_distribution_value[0],
        })
        return analytic_distribution_value

    def separate_analytic_service(self):
        warehouse_id, _ , center_id, transfer_center_id = self._get_warehouse_and_centers()
        self._update_warehouse_and_compute_transfer(warehouse_id)
        analytic_distribution_value = self._get_analytic_value(center_id, transfer_center_id)
        self._update_analytic_value(analytic_distribution_value[0])
        return warehouse_id, analytic_distribution_value[1]

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        if self.company_id.right_sale:
            warehouse_id, analytic_distribution = self.separate_analytic_service()
            values.update({
                'warehouse_id': warehouse_id,
                'analytic_distribution': self._format_analytic_distribution(analytic_distribution),
            })
        else:
            values['warehouse_id'] = self.order_id.warehouse_id
            if not self.warehouse_id:
                self.with_user(SUPERUSER_ID).write({
                    'warehouse_id': self.order_id.warehouse_id.id,
                })
        return values

    def _retrieve_purchase_partner(self):
        """ In case we want to explicitely name a partner from whom we want to buy or receive products
        """
        self.ensure_one()
        sale_center_product_id = self.env['sale.center.product.line'].search([
            ('center_id.company_id', '=', self.company_id.id),
            ('center_id.warehouse_id', '=', self.order_id.warehouse_id.id),
            ('product_id', '=', self.product_id.id)
         ])
        if sale_center_product_id:
            return sale_center_product_id.partner_id
        return False

    def _purchase_service_prepare_order_values(self, supplierinfo):
        values = super(SaleOrderLine, self)._purchase_service_prepare_order_values(supplierinfo)
        if self.company_id.right_sale:
            # warehouse_id, center_line_id, center_id, transfer_center_id = self._get_warehouse_and_centers()
            # if not center_line_id.partner_id.id:
            #     raise ValidationError((
            #         f"Please define a subcon Vendor for {self.product_id.display_name} in {self.order_id.warehouse_id.name} center table "
            #     ))
            values.update({'is_subcontract':True,'date_order': self.order_id.date_order})
        return values

    def _purchase_service_prepare_line_values(self, purchase_order, quantity=False):
        values = super(SaleOrderLine, self)._purchase_service_prepare_line_values(purchase_order,quantity)
        values['analytic_distribution'] = self.analytic_distribution
        return values
