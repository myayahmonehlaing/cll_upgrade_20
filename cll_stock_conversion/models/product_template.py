# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command,fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_convertible = fields.Boolean("Is Convertible")
    converted_product_id = fields.Many2one('product.product',string="Converted Product")
    is_general = fields.Boolean("Is General Product")
