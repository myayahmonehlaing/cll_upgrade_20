# -*- coding: utf-8 -*-


from odoo import models, fields, api, _,Command
from odoo.exceptions import UserError

class EmployeeHandoverRequest(models.Model):
    _name = 'employee.handover.request'
    _inherit = ["mail.thread", "mail.activity.mixin", "approval.mixin"]
    _description = 'User Handover Request'
    _order = 'date,id'

    approval_activity = "cll_employee_access_control.mail_activity_data_handover_request"

    name = fields.Char(string='Name')
    date = fields.Date(string='Date',default=fields.Date.context_today)
    # Add your custom fields and methods here
    workspace_email = fields.Char(string='Workspace Email')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    fingerprint_id = fields.Char(string='Fingerprint ID', related='employee_id.x_studio_fingerprint_id')
    job_id = fields.Many2one(comodel_name='hr.job', string='Position', check_company=True, related='employee_id.job_id')
    department_id = fields.Many2one(comodel_name='hr.department', string='Department', check_company=True, compute='_compute_department_id', store=True)
    system_ids = fields.Many2many(comodel_name='cll.system', string='System')
    handover_employee_id = fields.Many2one(comodel_name='hr.employee', string='Handover Employee')
    resignation_date = fields.Date(string='Resignation Date')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    state = fields.Selection(
        [
            ("draft", "To Submit"),
            ("submit", "Submitted for Approval"),
            ("confirm", "To Approve"),
            ("approve", "Approved"),
            ("refuse", "Refused"),
            ("cancel", "Cancelled"),
            ("acknowledge", "Acknowledge"),
            ("done", "Done"),
        ],
        string="Status",
        tracking=True,
        copy=False,
        readonly=False,
        default="draft",
        help="The status is set to 'To Submit', when a request is created."
        + "\nThe status is 'To Approve', when a request is confirmed by user."
        + "\nThe status is 'Refused', when a request is refused by manager."
        + "\nThe status is 'Approved', when a request is approved by manager.",
    )
    description = fields.Text(string="Description")
    can_edit = fields.Boolean(string='Can Edit', compute='_compute_can_edit', default=True)
    approval_condition_ids = fields.Many2many(
        "approval.condition",compute="_compute_approval_condition_ids",store=True,
    )


    @api.depends("system_ids")
    def _compute_approval_condition_ids(self):
        for request in self:
            if request.state != 'draft':
                continue

            request.approval_condition_ids = request.system_ids.mapped('property_handover_approval_id')


    @api.depends("employee_id")
    def _compute_department_id(self):
        for request in self:
            request.department_id = (
                request.employee_id.department_id if request.employee_id else False
            )
    def get_editable_states(self):
        return ['draft','confirm','submit',]

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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to set the name field."""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = (
                    self.env["ir.sequence"].sudo().next_by_code("employee.handover.request")
                )
        return super().create(vals_list)


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
            request.do_reset_approval()
            request.state = "draft"

    def action_cancel(self):
        for request in self:
            if request.approver_ids.filtered(
                lambda approver: approver.status == 'approve'
            ):
                raise UserError(
                    _("You cannot cancel this request because at least one approver has already approved it."))

            request.do_reset_approval()
            request.state = "cancel"

    def action_acknowledge(self):
        """Action to set the request to done state."""
        for request in self:
            request.state = "acknowledge"

    def action_done(self):
        """Action to set the request to done state."""
        system_status = self.env['employee.system.overview']
        for request in self:
            if request.system_ids:
                for system in request.system_ids:
                    system_id = system_status.search([
                            ("employee_id", "=", request.employee_id.id),
                             ("system_id", "=", system.id),
                        ])
                    if not system_id:
                        raise UserError(
                            _("The selected system (%s) does not have a related employee profile.") % system.name
                        )
                    else:
                        system_id.write({
                            'inactive_date': fields.Datetime.today(),
                            'status': 'inactive',
                        })
                        request.message_post(
                            body=_("Record has been marked as Inactive ") + request._get_html_link(),
                            message_type='comment',
                            subtype_xmlid='mail.mt_comment'
                        )
                    request.state = "done"

    def get_final_approve_state(self):
        vals = super().get_final_approve_state()
        vals.update({'acknowledge', 'done'})
        return vals

    @api.ondelete(at_uninstall=False)
    def _unlink_except_confirm(self):
        """Prevent deletion of posted or approved claims"""
        for request in self:
            if request.state != 'draft':
                raise UserError(_("You can delete only a draft request."))