from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ApprovalMixin(models.AbstractModel):
    _name = "approval.mixin"
    _description = "Reusable Approval Workflow Mixin"

    approval_activity = "cll_base_approval_rule.mail_activity_data_base_approval"
    refuse_reason = "cll_base_approval_rule.approval_template_refuse_reason"

    def _get_approval_rule(self):
        approval_rule = self.env["approval.rule"].search(
            [("model_id", "=", self._name), ("company_id", "=", self.env.company.id)]
        )
        if not approval_rule and self.use_approval:
            raise UserError(_("Approval Rule not found"))
        return approval_rule

    def _optional_approver_id_domain(self):
        approval_rule = self._get_approval_rule()
        optional_conditions = approval_rule.condition_ids.filtered(
            lambda a: a.condition_type == "optional"
        )
        optional_approver_ids = optional_conditions.optional_approver_ids.ids
        return [("id", "in", optional_approver_ids)]

    def _optional_approval_condition_ids_domain(self):
        approval_rule = self._get_approval_rule()
        condition_ids = approval_rule.condition_ids.filtered(
            lambda a: not a.mandatory
        ).ids
        return [("id", "in", condition_ids)]

    def _compute_use_approval(self):
        """Overwrite in order to overwrite company configuration to use approval"""
        # return NotImplementedError(_("This function is not implemented"))
        for record in self:
            record.use_approval = False

    use_approval = fields.Boolean(
        string="Is Used Approval", compute="_compute_use_approval"
    )

    approver_ids = fields.One2many(
        "approval.approver.approver",
        "record_id",
        string="Approvers",
        domain=lambda self: [("model_name", "=", self._name)],
    )

    user_status = fields.Selection(
        [
            ("new", "New"),
            ("submit", "To Approve"),
            ("waiting", "Waiting"),
            ("approve", "Approved"),
            ("done", "Paid"),
            ("post", "Posted"),
            ("cancel", "Refused"),
        ],
        compute="_compute_user_status",
    )

    approval_rule_id = fields.Many2one(
        "approval.rule",
        default=lambda self: self._get_approval_rule(),
    )
    optional_approver_id = fields.Many2one(
        "res.users",
        domain=_optional_approver_id_domain,
        store=True,
    )
    approval_condition_ids = fields.Many2many(
        "approval.condition",
        domain=_optional_approval_condition_ids_domain,
        store=True,
    )
    approval_condition_status = fields.Char(
        "Approval Status",
        compute="_compute_approval_status" )
    approval_date = fields.Datetime(string="Approval Date", readonly=True)
    can_cancel = fields.Boolean(string="Can Cancel" , compute="_compute_can_cancel" )

    def _compute_can_cancel(self):
        for record in self:
            record.can_cancel = (( record.create_uid == self.env.user ) and
                not any(record.approver_ids.filtered(lambda approver: approver.status == 'approve')))


    @api.constrains("approver_ids")
    def _check_unique_approvers(self):
        for record in self:
            approver_ids = record.approver_ids
            if len(approver_ids) != len(set(approver_ids.mapped("user_id.id"))):
                raise ValidationError(
                    " You cannot assign the same approver multiple times "
                )

    @api.depends("approver_ids.status")
    def _compute_user_status(self):
        for record in self:
            record.user_status = record.approver_ids.filtered(
                lambda approver: approver.user_id == self.env.user
            ).status

    def get_final_approve_state(self):
        return {'approve','post','posted','done','validate1'}


    @api.depends("approver_ids.status",)
    def _compute_approval_status(self):
        """
        Compute the approval condition status based on approvers' states.

        - If exactly one approver is in 'submit' status, show waiting message.
        - If all approvers have approved and state is not 'draft', mark as 'All Approved'.
        - Otherwise, set status as 'to submit'.
        """
        def get_approver(status=False):
            return (
                record.approver_ids.filtered(lambda r: r.status == status)
                if status
                else record.approver_ids
            )

        for record in self:
            approvers_to_approve = get_approver("submit")
            approved_count = len(get_approver("approve"))
            total_approvers = len(get_approver())
            condition_status = "To Submit"

            if approvers_to_approve:
                condition_status = (
                    f"Waiting {approvers_to_approve[0].name} Approval"
                )
            elif record.state in self.get_final_approve_state() and approved_count == total_approvers:
                condition_status = "All Approved"
            elif record.state in ("refused","refuse"):
                approvers_refused = get_approver("cancel")
                condition_status = f" {approvers_refused[0].name} Refused" if approvers_refused else "Refused"
            elif record.state == "cancel":
                condition_status = "Cancelled"
            record.approval_condition_status = condition_status

    def _get_approval_activity(self):
        return self.approval_activity

    def get_subtype(self):
        """
        Return the mail subtype ID for comments (mail.mt_comment).
        """
        return self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_comment")

    def _create_approvers(self, amount):
        if not self.approval_rule_id:
            return

        val = approver_vals = []
        lines = (
                self.approval_rule_id.condition_ids.filtered("mandatory")
                | self.approval_condition_ids
        )
        user_sets = set()
        for condition in lines.sorted("sequence"):
            employee_id = False
            if hasattr(self, "employee_id"):
                employee_id = self.employee_id
            elif hasattr(self, "employee1_id"):
                employee_id = self.employee1_id

            val = condition._get_approver_val(
                employee_id= employee_id,
                optional_approver_id=self.optional_approver_id,
                amount=amount,
                currency_id=self.currency_id if hasattr(self, "currency_id") else False,
                partner_id=(
                    self.partner_id if hasattr(self, "partner_id") and (hasattr(self, "is_employee_advance")
                    and self.is_employee_advance  ) else self.create_uid.partner_id
                ),
            )

            if isinstance(val, list):  # Multiple vals
                approver_vals.extend(
                    (0, 0, {
                        **v,
                        "model_name": self._name,
                        "record_id": self.id
                    })
                    for v in val
                    if v["user_id"] not in user_sets and not user_sets.add(v["user_id"])
                )
            # else:  # Single val
            #     approver_vals.append(
            #         (0, 0, {**val, "model_name": self._name, "record_id": self.id})
            #     )

        if approver_vals:
            self.write({"approver_ids": approver_vals})

    def get_related_approvers(self, approvers):
        """Get related approvers"""
        related_approvers = self.env["approval.approver.approver"]
        if approvers:
            related_approvers |= self.approver_ids.filtered(
                lambda a: a.condition_id == approvers.condition_id
                and not a.id == approvers.id
            )
        return related_approvers

    def process_approval_create(self, amount):
        """Overwrite to carry total amount in order to get approver by balance"""
        self._create_approvers(amount=amount)
        approvers = self.approver_ids
        if not approvers:
            raise UserError(
                _("You have to add at least one approver to submit expense request.")
            )
        approvers = approvers.filtered(
            lambda a: a.status in ["new", "submit", "waiting"]
        ).sorted(key=lambda a: a.id)
        approvers[1:].sudo().write({"status": "waiting"})
        approvers = (
            approvers[0]
            if approvers and approvers[0].status != "submit"
            else self.env["approval.approver.approver"]
        )
        approvers |= self.get_related_approvers(approvers)
        return approvers.sudo().write({"status": "submit"})

    def action_submit(self):
        """
        Submit the requrest for approval by creating approvers,
        updating their statuses, and scheduling approval activities.
        """
        self.process_approval_create(amount=0.0)
        return self.do_submit()

    def action_withdraw(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.approver_ids.filtered(
                lambda a: a.user_id == self.env.user
            )
            if not approver:
                raise ValidationError(_("You are not an approver of this request."))
            approver.ensure_one()
            next_approver = self.approver_ids.filtered(
                lambda a: a.status in ("approve",'refuse') and a.id > approver.id
            )
            if next_approver:
                raise ValidationError(
                    _("Sorry, you are not allowed to withdraw after a subsequent approver has approved.")
                )

        self.sudo()._update_next_approvers('waiting', approver, only_next_approver=False, cancel_activities=True)
        approver.write({'status': 'submit'})
        self.message_post(body=_("%s withdrew their approval.") % approver.user_id.name,)

    def _cancel_activities(self):
        approval_activity = self.env.ref(self._get_approval_activity())
        activities = self.activity_ids.filtered(lambda a: a.activity_type_id == approval_activity)
        activities.unlink()

    def _get_user_approval_activities(self, user):
        domain = [
            ("res_model", "=", self._name),
            ("res_id", "in", self.ids),
            ("activity_type_id", "=", self.env.ref(self._get_approval_activity()).id),
            ("user_id", "=", user.id),
        ]
        activities = self.env["mail.activity"].search(domain)
        return activities

    def _update_next_approvers(self, new_status, approver, only_next_approver, cancel_activities=False):
        approvers_updated = self.env["approval.approver.approver"]

        current_approver = self.approver_ids & approver
        current_approver = current_approver.filtered(
            lambda a: a.user_id == self.env.user
        )
        approvers_to_update = self.approver_ids.filtered(
            lambda a: a.status not in ["approve", "refuse"]
            and (a.id > current_approver.id)
        )

        if only_next_approver and approvers_to_update:
            approvers_to_update = approvers_to_update[0]
            approvers_to_update |= self.get_related_approvers(approvers_to_update)
        approvers_updated |= approvers_to_update

        approvers_updated.sudo().status = new_status
        if cancel_activities:
            self._cancel_activities()

    def action_approve_batch_request(self):
        for record in self:
            if record.user_status != "submit":
                raise ValidationError(_('Sorry, you are not allowed to approve this document( ID:%s )yet.') % record.id)
            record.approve_approval_approver()

    def approve_approval_approver(self, approver=None):
        """
        Approve the record  by the current approver.

        Updates approver status, triggers next approval step, posts messages,
        and posts the move when fully approved.
        """
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped("approver_ids").filtered(
                lambda approver: approver.user_id == self.env.user
            )
        related_approver = self.get_related_approvers(approver)
        if related_approver:
            for r_approver in related_approver:
                self.sudo()._get_user_approval_activities(
                    user=r_approver.user_id
                ).unlink()
            approver |= related_approver
        approver.write({"status": "approve"})

        self.sudo()._update_next_approvers("submit", approver, only_next_approver=True)
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

        status_lst = self.mapped("approver_ids.status")
        approvers = len(status_lst)
        if status_lst.count("approve") == approvers:
            return self.action_approver_approve()
        return None

    def action_approver_approve(self):
        """Action to approve approver status"""
        return self.do_approve()

    def do_refuse(self, reason, approver=None):
        """Refuse Approval with reason"""
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped("approver_ids").filtered(
                lambda approver: approver.user_id == self.env.user
            )
        related_approver = self.get_related_approvers(approver)
        if related_approver:
            for r_approver in related_approver:
                self.sudo()._get_user_approval_activities(
                    user=r_approver.user_id
                ).unlink()
            approver |= related_approver
        if approver:
            approver.write({"status": "cancel"})
            self.sudo()._get_user_approval_activities(
                user=self.env.user
            ).action_feedback()
            if not self.env.context.get("skip_reject_message"):
                subject_name = self.name if (hasattr(self,"name")
                                             and self.name and self.name != "/") else "Your Approval"
                subject = f"{subject_name} has been refused"
                self.message_post_with_source(
                    self.refuse_reason,
                    subtype_id=self.get_subtype(),
                    render_values={"reason": reason, "name": subject_name},
                    subject=subject,
                )

        return self.write({"state": "refuse" if 'refuse' in dict(self._fields['state'].selection) else "cancel"})

    def do_submit(self):
        """Change state to submit for model"""
        self.write({"state": "submit"})

    def do_approve(self):
        """Change state to approve with approval date"""
        for record in self.filtered(lambda s: s.state == 'submit'):

            record.write(
                {
                    "state": "approve",
                    "approval_date": fields.Date.context_today(record),
                }
            )

    def do_reset_approval(self):
        """Reset approval steps and unlink approval activity"""
        for record in self:
            record.approver_ids.unlink()
            record.activity_unlink([record._get_approval_activity()])

    def action_reset_approval(self):
        """Action to call from views"""
        self.do_reset_approval()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('approval_rule_id') and ( vals.get('employee_id') or vals.get('employee1_id')):
                employee_id = self.env['hr.employee'].browse([vals.get('employee_id') or vals.get('employee1_id')])
                approval_rule = self.env["approval.rule"].search(
                    [("model_id", "=", self._name), ("company_id", "=", employee_id.company_id.id)]
                )
                vals['approval_rule_id'] = approval_rule.id if approval_rule else False
        return super(ApprovalMixin, self).create(vals_list)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = domain or []

        if 'approval_condition_status' in groupby:
            records = self.search(domain)

            result = {}
            domain_map = {}

            for rec in records:
                key = rec.approval_condition_status
                result.setdefault(key, 0)
                result[key] += 1

                # Build domain per group
                if key not in domain_map:
                    domain_map[key] = self._domain_from_approval_status(key)

            return [
                {
                    'approval_condition_status': key,
                    '__count': count,
                    '__domain': domain_map[key],
                }
                for key, count in result.items()
            ]

        return super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)


    def _domain_from_approval_status(self, approval_status):
        status = (approval_status or '').lower()
        words = status.split()

        name = (
            " ".join(words[1:-1]) if status.startswith('waiting') and len(words) > 2 else
            " ".join(words[:-1]) if status.endswith('refused') and len(words) > 1 else
            status
        )
        if status.startswith('waiting'):
            return [
                ('approver_ids', 'any', [
                    ('name', 'ilike', name),
                    ('status', '=', 'submit'),
                ]),
                ('state', 'not in', list(self.get_final_approve_state())),
            ]

        if status.endswith('refused') and len(words) >= 2 :
            return [
                ('approver_ids', 'any', [
                    ('name', 'ilike', name),
                    ('status', '=', 'cancel'),
                ]),
                ('state', '=', 'refuse'),
            ]

        if status == 'all approved':
            return [('state', 'in', list(self.get_final_approve_state()))]

        if 'refused' in status:

            return [('state', '=', 'refuse'), ('approver_ids', '=', False)]

        if 'cancelled' in status:
            return [('state', '=', 'cancel')]

        if status == 'to submit':
            status =  ['draft', 'confirm']
            if self._name == 'hr.attendance.request':
                status.extend(['validate'])
            if self._name in ('overtime.request','duty.swap'):
                status.extend(['approve1'])
            return [('state', 'in', status)]

        return [('id', '=', 0)]


