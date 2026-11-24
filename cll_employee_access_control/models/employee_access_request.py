# -*- coding: utf-8 -*-


from odoo import models, fields, api, _,Command
from odoo.exceptions import UserError

class EmployeeAccessRequest(models.Model):
    _name = 'employee.access.control'
    _inherit = ["mail.thread", "mail.activity.mixin", "approval.mixin"]
    _description = 'Employee Access Control'
    _order = 'name desc'



    approval_activity = "cll_employee_access_control.mail_activity_data_user_request"

    name = fields.Char(string='Name',copy=False)
    date = fields.Date(string='Date',default=fields.Date.context_today,copy=False)
    workspace_email = fields.Char(string='Primary Mail')
    request_type = fields.Selection(string="Request Type",selection=[('create', 'Create'), ('update', 'Update')],default= 'create')
    workspace_type = fields.Selection(string="Workspace Type",selection=[('primary', 'Primary Mail'), ('alias', 'Alias Mail')],default=False)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',required=True)
    fingerprint_id = fields.Char(string='Fingerprint ID', related='employee_id.x_studio_fingerprint_id')
    system_tag = fields.Many2one(comodel_name='cll.system.tag', string='System Tag')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    email = fields.Char(string='Employee Email', compute='_compute_employee_email', store=True)
    job_id = fields.Many2one(comodel_name='hr.job', string='Position', check_company=True, related='employee_id.job_id')
    department_id = fields.Many2one(comodel_name='hr.department', string='Department', check_company=True, compute='_compute_department_id', store=True)

    system_id = fields.Many2one(comodel_name='cll.system', string='System',required=True)
    access_companies = fields.Many2many('cll.company', string='Access Companies')
    access_facilities = fields.Many2many('cll.facility', string='Access Facilities')
    group_ids = fields.Many2many('cll.system.role', string='Roles',default=lambda s: s._default_groups())

    remark = fields.Text(string='Remark')
    state = fields.Selection(
        [
            ("draft", "To Submit"),
            ("confirm", "To Approve"),
            ("submit", "Submitted for Approval"),
            ("validate1", "Second Approval"),
            ("refuse", "Refused"),
            ("approve", "Approved"),
            ("vendor_action", "Waiting for Vendor"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        store=True,
        tracking=True,
        copy=False,
        readonly=False,
        default="draft",
        help="The status is set to 'To Submit', when a request is created."
        + "\nThe status is 'To Approve', when a request is confirmed by user."
        + "\nThe status is 'Refused', when a request is refused by manager."
        + "\nThe status is 'Approved', when a request is approved by manager.",
    )
    is_privileged_required = fields.Boolean(string="Required Privileged Access")
    approval_condition_ids = fields.Many2many(
        "approval.condition",compute="_compute_approval_condition_ids",store=True,
    )
    is_odoo = fields.Boolean(string='Is Odoo System',related='system_id.is_odoo')
    is_workspace = fields.Boolean(string='Is Workspace System', related='system_id.is_workspace')
    can_edit = fields.Boolean(string='Can Edit', compute='_compute_can_edit',default=True)
    description = fields.Text(string="Description")

    @api.depends("system_id", "is_privileged_required")
    def _compute_approval_condition_ids(self):
        approval_condition_ids = self.env["approval.condition"]
        for request in self:
            if request.state != 'draft':
                continue

            if request.system_id:
                approval_condition_ids |= request.system_id.property_request_approval_id

            if request.is_privileged_required:
                privileged = request.approval_rule_id.condition_ids.filtered(lambda c: c.condition_type != 'optional'
                        and not c.mandatory).sorted(key=lambda c: c.sequence)
                approval_condition_ids |= privileged[0]
            request.approval_condition_ids = approval_condition_ids



    @api.model
    def _default_groups(self):
        return self.env['cll.system.role'].search([("is_default", "=", True)])

    @api.model_create_multi
    def create(self, vals):
        """Override create method to set the name field."""
        for val in vals:
            if not val.get("name"):
                val["name"] = (
                    self.env["ir.sequence"].sudo().next_by_code("employee.access.control")
                )
        return super().create(vals)


    @api.depends("employee_id")
    def _compute_department_id(self):
        for request in self:
            request.department_id = (
                request.employee_id.department_id if request.employee_id else False
            )

    @api.depends("employee_id")
    def _compute_employee_email(self):
        for request in self:
            request.email = (
                request.employee_id.work_email if request.employee_id else False
            )

    @api.model
    def default_get(self, fields):
        """Overwrite for default value of company setting approval usage flag"""
        rec = super().default_get(fields)
        if "use_approval" in fields:
            rec["use_approval"] = True
        return rec

    def get_editable_states(self):
        return ['draft','confirm','submit','validate1']

    def _compute_use_approval(self):
        """Compute whether to use approval workflow based on company settings"""
        for request in self:
            request.use_approval = True

    def _compute_can_edit(self):
        user = self.env.user
        can_edit = False
        for request in self:
            if request.user_status == "approve":
                can_edit = False
            if (user in request.approver_ids.mapped('user_id')
                    and not request.user_status in ("approve","cancel")
                    and request.state in request.get_editable_states()
            ):
                can_edit = True
            if request.state == 'draft':
                can_edit = True

            request.can_edit = can_edit


    @api.ondelete(at_uninstall=False)
    def _unlink_except_posted_or_approved(self):
        """Prevent deletion of posted or approved claims"""
        for request in self:
            if request.state in {"done", "approve"}:
                raise UserError(_("You cannot delete a posted or approved request."))

    def action_confirm(self):
        """Action to reset the request to draft state."""
        for request in self:
            if request.state not in {"approve"}:
                request.do_reset_approval()
                request.state = "confirm"

    def do_refuse(self, reason, approver=None):
        record = super().do_refuse(reason, approver=approver)
        self.write({"remark": reason})
        return record

    def action_draft(self):
        """Action to reset the request to draft state."""
        for request in self:
            request.state = "draft"
            request.do_reset_approval()


    def action_cancel(self):
        for request in self:
            if request.approver_ids.filtered(
                lambda approver: approver.status == 'approve'
            ):
                raise UserError(
                    _("You cannot cancel this request because at least one approver has already approved it."))

            request.do_reset_approval()
            request.state = "cancel"

    def action_done(self):
        """Action to set the request to done state."""
        system = self.env['employee.system.overview']
        for request in self:
            if request.request_type == 'create':
                system_id = system.search([
                        ("employee_id", "=", request.employee_id.id),
                        ("system_id", "=", request.system_id.id),
                    ])
                if system_id:
                    raise UserError(
                        _("Employee has been already recorded."))
                else:
                    overview_id = system.create({
                        'employee_id': request.employee_id.id,
                        'system_id': request.system_id.id,
                        'active_date': fields.Datetime.today(),
                        'status': 'active',
                    })
                    request.message_post(
                        body=_("Record has been created ") + overview_id._get_html_link(),
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment'
                    )
            request.state = "done"

    # Add this method to get admin emails based on system
    def _get_system_emails(self):
        """Get admin emails from cll.mail.config for the selected system"""
        self.ensure_one()
        if not self.system_id:
            return []

        # Return partner emails
        return self.system_id.partner_ids

    def _find_mail_template(self):
        """Find the appropriate email template for user request"""
        self.ensure_one()
        template = self.env.ref('cll_employee_access_control.email_template_employee_access_approved', raise_if_not_found=False)
        return template

    def action_send_admin_notification(self):
        """Opens a wizard to compose an email to system admins"""
        self.ensure_one()
        
        # Get admin emails from configuration
        partner_ids = self._get_system_emails()

        if not partner_ids:
            raise UserError(_("No admin contacts configured for this system."))

        # Find the appropriate template
        mail_template = self._find_mail_template()
        
        # Get the right language
        lang = self.env.context.get('lang')
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]

        # Prepare context for the composer
        ctx = {
            'default_model': 'employee.access.control',
            'default_res_ids': self.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'default_partner_ids': partner_ids.ids,
            'force_email': True,
            'mark_user_request_as_notified': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'model_description': self.with_context(lang=lang)._description,
            'custom_layout': 'mail.mail_notification_light',
        }
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def get_final_approve_state(self):
        vals = super().get_final_approve_state()
        vals.update({'vendor_action', 'done'})
        return vals

    @api.ondelete(at_uninstall=False)
    def _unlink_except_confirm(self):
        """Prevent deletion of posted or approved claims"""
        for request in self:
            if request.state != 'draft':
                raise UserError(_("You can delete only a draft request."))
