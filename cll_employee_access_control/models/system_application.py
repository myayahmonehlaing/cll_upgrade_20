# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from random import randint


class CllCompany(models.Model):
    _name = 'cll.company'
    _description = 'CLL Company'

    name = fields.Char(string='Name', required=True)


class CllFacility(models.Model):
    _name = 'cll.facility'
    _description = 'CLL Facility'

    name = fields.Char(string='Name', required=True)

class CllSystem(models.Model):
    _name = 'cll.system'
    _description = 'CLL System'

    def _approval_request_condition_domain(self):
        condition_ids = self.env['approval.condition'].search(
            [("rule_id.model_id.model", "=",'employee.access.control'),("mandatory", "=", False)]
        )
        return [("id", "in", condition_ids.ids)] if condition_ids else None

    def _approval_handover_condition_domain(self):
        condition_ids = self.env['approval.condition'].search(
            [("rule_id.model_id.model", "=",'employee.handover.request'),("mandatory", "=", False)]
        )
        return [("id", "in", condition_ids.ids)] if condition_ids else None

    name = fields.Char(string='System Name', required=True)
    image = fields.Binary(string='Image',store=True)
    description = fields.Text(string='Description')

    tag_ids = fields.Many2many(comodel_name='cll.system.tag', string='Tags')
    is_odoo = fields.Boolean(string='Is Odoo System', default=False)

    is_workspace = fields.Boolean(string='Is Workspace System', default=False)

    user_type = fields.Selection(
        selection=[('light', 'Light User'), ('standard', 'Standard User')], string='User Type'
    )

    partner_ids = fields.Many2many(comodel_name='res.partner', string='Recepients', help='Partners to notify for this system.')
    active = fields.Boolean(string='Is Active', default=True)
    property_request_approval_id = fields.Many2one(comodel_name='approval.condition', string='Request Approver',
                                            domain=_approval_request_condition_domain,company_dependent=True,)
    property_handover_approval_id = fields.Many2one(comodel_name='approval.condition', string='Handover Approver',
                                                    domain=_approval_handover_condition_domain,company_dependent=True,)
    licensed_users = fields.Integer("Total Licensed Users")

    def get_system_info(self):
        """Return system information as a dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'tags': self.tag_ids.mapped('name'),
            'is_odoo': self.is_odoo,
        }

class CllSystemTag(models.Model):
    _name = 'cll.system.tag'
    _description = 'CLL System Tag'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True)
    description = fields.Text(string='Description')

    color = fields.Integer(string='Color', default=_get_default_color)

class SystemApplication(models.Model):
    _name = 'cll.system.application'
    _description = 'Applications'

    name = fields.Char(string='Application Name', required=True)
    description = fields.Text(string='Description')
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    system_id = fields.Many2one(comodel_name='cll.system', string='System')

    @api.depends('name', 'system_id')
    def _compute_display_name(self):
        for application in self:
            application.display_name = f'{application.name} ( {application.system_id.name} )'

class SystemRoles(models.Model):
    _name = 'cll.system.role'
    _description = 'Application Roles'
    _order = 'application_sequence, sequence, name'

    name = fields.Char(string='Name', required=True)
    application_id = fields.Many2one(comodel_name='cll.system.application', string='Application')
    description = fields.Text(string='Description')
    system_id = fields.Many2one(comodel_name='cll.system', string='System', required=True,
                              store=True , readonly=False , compute='_compute_system_id')

    # Type field - determines if it's selection (application) or checkbox (extra)
    display_type = fields.Selection(
        selection=[
            ('selection', 'Selection (Application Role)'),
            ('checkbox', 'Checkbox (Privileged Access)')
        ],
        string='Display Type',
        default='selection',
        required=True
    )
    
    # For ordering
    application_sequence = fields.Integer(
        string='App Sequence',
        related='application_id.sequence',
        store=True,
        readonly=True
    )
    sequence = fields.Integer(string='Sequence', default=10)

    # Access control fields
    is_technical = fields.Boolean(
        string='Technical',
        default=False,
        help='Technical roles are only visible to administrators'
    )

    # For UI purposes
    is_default = fields.Boolean(
        string='Default Role',
        default=False,
        help='Default role for this application'
    )
    
    active = fields.Boolean(string='Active', default=True)

    _code_uniq = models.Constraint(
        'UNIQUE(code)',
        "Role code must be unique!",
    )

    _name_app_uniq = models.Constraint(
        'UNIQUE(name, application_id)',
        "Role name must be unique per application!",
    )

    @api.constrains('is_default')
    def _check_default_role(self):
        """Ensure only one default role per application and display type."""
        for record in self:
            if record.is_default:
                existing_default = self.search([
                    ('application_id', '=', record.application_id.id),
                    ('display_type', '=', record.display_type),
                    ('is_default', '=', True),
                    ('id', '!=', record.id)
                ])
                if existing_default:
                    raise ValidationError(
                        f'Only one {record.display_type} role can be default '
                        f'for application {record.application_id.name}'
                    )

    @api.model
    def create(self, vals):
        """Override create to update user request view when new role is created."""
        res = super().create(vals)
        # Update both views if needed
        self.env['employee.access.control'].sudo()._update_user_request_view()
        return res
    
    def write(self, vals):
        """Override write to update view when role is modified."""
        view_related_fields = {'name', 'display_type', 'application_id', 'sequence', 'active'}
        if any(field in vals for field in view_related_fields):
            res = super().write(vals)
            self.env['employee.access.control'].sudo()._update_user_request_view()
            return res
        return super().write(vals)
    
    def unlink(self):
        """Override unlink to update view when role is deleted."""
        res = super().unlink()
        self.env['employee.access.control'].sudo()._update_user_request_view()
        return res

    @api.depends("application_id")
    def _compute_system_id(self):
        for record in self:
            record.system_id = record.application_id.system_id if record.application_id else False