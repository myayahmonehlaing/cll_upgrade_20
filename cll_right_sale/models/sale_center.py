# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class SaleCenter(models.Model):
    _name = 'sale.center'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sale Center configuration for Product from Charm to Odoo"

    name = fields.Char(string='Item Name')
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Warehouse', check_company=True)
    user_ids = fields.Many2many(comodel_name='res.users', relation='sale_center_res_user_rel', string='Users', check_company=True)
    center_line_ids = fields.One2many(comodel_name='sale.center.product.line', inverse_name='center_id', string='Product Lines')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.company)
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Distribution', check_company=True)
    active = fields.Boolean(string='Is Active', default=True)

class SaleCenterProductLine(models.Model):
    _name = 'sale.center.product.line'
    _description= "Sale Center Lines"

    sequence = fields.Integer(string='Sequence', default=10)
    center_id = fields.Many2one(comodel_name='sale.center', string='Work Center', check_company=True)
    product_code = fields.Char(string='Product Code (Charm)', required=True)
    product_name = fields.Char(string='Description')
    product_id = fields.Many2one(comodel_name='product.product', string='Product Code (Odoo)', required=True, check_company=True)
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse', string='Destination', check_company=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Subcon Vendor', check_company=True)
    company_id = fields.Many2one(comodel_name='res.company', related='center_id.company_id', store=True)
