# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class EmployeeSystemOverview(models.Model):
    _name = 'employee.system.overview'
    _description = 'System Overview'

    name = fields.Char(string='Name',compute='_compute_name',store=True, readonly=False, precompute=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    department_id = fields.Many2one(comodel_name='hr.department', related='employee_id.department_id', store=True)
    job_id = fields.Many2one(comodel_name='hr.job', related='employee_id.job_id', store=True)
    company_id = fields.Many2one(comodel_name='res.company',related='employee_id.company_id', store=True)
    system_id = fields.Many2one(comodel_name='cll.system', string='System')
    status = fields.Selection(selection=[
        ('active', "Active"),
        ('inactive', "Inactive"),
    ], string="Status")
    active_date = fields.Date('Active Date')
    inactive_date = fields.Date('Inactive Date')

    @api.depends('employee_id','system_id')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.system_id:
                record.name = record.employee_id.name + ' - ' + record.system_id.name

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

    def get_action_spreadsheet_dashboard(self):
        dashboard = self.env.ref('cll_employee_access_control.spreadsheet_dashboard_system_overview')
        return {
            "type": "ir.actions.client",
            "tag": "action_spreadsheet_dashboard",
            "name": self.name,
            "params": {
                "dashboard_id": dashboard.id,
            },
        }

