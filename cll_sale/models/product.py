"""Extension of Product Models."""

# pylint: disable=import-error,too-few-public-methods
from odoo import fields, models


class ProductTemplate(models.Model):
    """Extension of Product Template Model."""

    _inherit = "product.template"

    # company_id = fields.Many2one(
    #     "res.company",
    #     "Company",
    #     index=True,
    #     default=lambda self: self.env.company if self.env.company.id == 1 else False,
    # )

    retail_class_id = fields.Many2one('product.retail.class',string="Retail Class")
    retail_size_ids = fields.Many2many('product.retail.size',string="Retail Store Sizes" )


class Product(models.Model):
    """Extension of Product Model."""

    _inherit = "product.product"


class RetailClass(models.Model):

    _name = "product.retail.class"
    _description = 'Retail Class'

    name = fields.Char()



class RetailSize(models.Model):

    _name = "product.retail.size"
    _description = 'Retail Store Size'

    name = fields.Char()