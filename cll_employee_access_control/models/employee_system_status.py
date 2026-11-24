# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class EmployeeSystemStatus(models.Model):
    _name = 'employee.system.status'
    _description = 'Employee System Status'

    name = fields.Char(string='Name')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    department_id = fields.Many2one(comodel_name='hr.department', related='employee_id.department_id', store=True)
    company_id = fields.Many2one(comodel_name='res.company',related='employee_id.company_id', store=True)
    system_id = fields.Many2one(comodel_name='cll.system', string='System')
    is_active = fields.Boolean('Active',default=True)
    active_date = fields.Date('Active Date')
    inactive_date = fields.Date('Inactive Date')

    @api.constrains('employee_id', 'system_id')
    def _constrains_employee_system_unique(self):
        for record in self:
            if not record.employee_id or not record.system_id:
                continue

            duplicates = self.search([
                ('employee_id', '=', record.employee_id.id),
                ('system_id', '=', record.system_id.id),
                ('id', '!=', record.id),
            ], limit=1)

            if duplicates:
                raise ValidationError(_(
                    "The employee '%(employee)s' is already assigned to the system '%(system)s'.",
                    employee=record.employee_id.name,
                    system=record.system_id.display_name,
                ))

