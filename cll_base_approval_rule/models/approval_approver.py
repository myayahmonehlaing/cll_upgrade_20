from odoo import api, fields, models


class ApprovalApproverApprover(models.Model):
    """
    Model representing approvers for approval.approver with status tracking
    and activity scheduling for approval workflow.
    """

    _name = "approval.approver.approver"
    _description = "Approval Approver"

    model_name = fields.Char(
        string="Model Name", help="Name of the model associated with this approval"
    )
    record_id = fields.Many2oneReference(
        model_field="model_name",
        string="Record ID",
        help="Reference to the record in the model",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
    )

    user_id = fields.Many2one(
        "res.users", string="User", required=True, check_company=True
    )
    name = fields.Char(string="Name")
    status = fields.Selection(
        [
            ("new", "New"),
            ("submit", "To Approve"),
            ("waiting", "Waiting"),
            ("approve", "Approved"),
            ("post", "Posted"),
            ("cancel", "Refused"),
            ("done", "Paid"),
        ],
        string="Status",
        default="new",
        readonly=True,
    )
    condition_id = fields.Many2one("approval.condition")

    @api.model_create_multi
    def create(self, vals_list):
        """Overwrite in order to update approval activity on Approval State"""
        records = super().create(vals_list)
        records.sudo().approval_activity_update()
        return records

    def write(self, vals):
        """Override write method to handle state changes and recompute related lines."""
        res = super().write(vals)
        if vals.get("status"):
            self.sudo().approval_activity_update()
        return res

    def get_activity_status(self):
        """Get activity status for reset draft activity unlink"""
        return ["draft", "cancel"]

    def get_approve_status(self):
        """Get activity status for reset draft activity unlink"""
        return ["approve"]

    def approval_activity_update(self):
        """Update activity according to State changes"""
        for approver in self:
            if approver.model_name and approver.record_id:
                record_id = (
                    self.env[approver.model_name].sudo().browse(approver.record_id)
                )
                if approver.status == "submit" and not self.env.context.get('skip_activity_schedule'):
                    record_id.sudo().activity_schedule(
                        record_id._get_approval_activity(), user_id=approver.user_id.id
                    )
                elif approver.status in self.get_approve_status():
                    record_id.sudo().activity_feedback(record_id._get_approval_activity())
                elif approver.status in self.get_activity_status():
                    record_id.sudo().activity_unlink(record_id._get_approval_activity())
