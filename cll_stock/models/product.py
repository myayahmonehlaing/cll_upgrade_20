from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_id = fields.Many2one(
        'res.company', 'Company', index=True,default=lambda self: self.env.company if self.env.company.id == 1 else False)


class Product(models.Model):
    _inherit = 'product.product'