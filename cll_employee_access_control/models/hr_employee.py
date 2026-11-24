# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api,fields, models
from odoo.exceptions import UserError

class Employee(models.Model):
    _inherit = "hr.employee"

    system_ids = fields.One2many('employee.system.overview','employee_id',"Systems")
    asset_request_ids = fields.One2many('hr.asset.request', 'employee_id', "Asset Requests")


class HrEmployees(models.Model):
    """Inherit the model to add fields and functions"""

    _inherit = "hr.employee.public"

    # system_ids = fields.One2many('employee.system.overview', 'employee_id', "Systems")
    # asset_request_ids = fields.One2many('hr.asset.request', 'employee_id', "Asset Requests")