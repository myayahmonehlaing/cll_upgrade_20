from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # company_id = fields.Many2one(
    #     'res.company', 'Company', index=True,default=lambda self: self.env.company if self.env.company.id == 1 else False)
