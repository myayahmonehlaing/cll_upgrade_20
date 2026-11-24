# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api,fields, models
from odoo.exceptions import UserError

class AssetRequest(models.Model):
    _name = "hr.asset.request"
    _description = "Asset Requests"

    name = fields.Char(string="Name")
    employee_id = fields.Many2one(comodel_name='hr.employee', required=True)
    department_id = fields.Many2one(comodel_name='hr.department', related='employee_id.department_id', store=True)
    company_id = fields.Many2one(comodel_name='res.company', related='employee_id.company_id', store=True)
    type = fields.Char(string="Type")
    onboard_date = fields.Datetime(string="Onboard Date")
    offboard_date = fields.Datetime(string="Offboard Date")
    remark = fields.Char(string="Remark")
