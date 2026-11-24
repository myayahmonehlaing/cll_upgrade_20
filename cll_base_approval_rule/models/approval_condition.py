"""
Approval Rules and Conditions

This module defines the models and logic for configuring approval rules,
conditions, and approvers within Odoo. It supports multiple types of conditions
(field-based, user-based, or optional), amount thresholds, and company-specific
rules.
"""

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.exceptions import UserError


class ApprovalConditon(models.Model):
    """Defines the conditions used within an approval rule."""

    _name = "approval.condition"
    _description = "Approval Condition"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(
        help="Used to order Condition in the tree view", default=10
    )
    mandatory = fields.Boolean()
    condition_type = fields.Selection(
        selection=[
            ("field", "By Field"),
            ("user", "By User"),
            ("optional", "Optional"),
        ],
        default="user",
        string="Type",
    )
    field_ids = fields.Many2many(
        "ir.model.fields", domain=[("model_id.model", "=", "hr.employee")]
    )

    rule_id = fields.Many2one("approval.rule")
    line_ids = fields.One2many(
        comodel_name="approval.condition.line", inverse_name="condition_id"
    )
    optional_approver_ids = fields.Many2many("res.users", string="Optional Approvers")
    company_id = fields.Many2one("res.company", "Company", related="rule_id.company_id")

    def _get_employee(self, employee, partner):

        if employee:
            return employee
        return (
            self.env["hr.employee"].sudo().search([("work_contact_id", "=", partner.id)])
            if partner
            else self.env["hr.employee"]
        )

    def _get_approver_val(self, **data):
        employee = self._get_employee(data.get("employee_id"), data.get("partner_id"))
        if not employee :
            raise UserError(
                _('The selected partner "%s" is not linked to any employee.')
                % employee.name
            )

        users_dict = {}
        if self.condition_type == "field":
            # map field-based users
            users_dict[self.name] = self.field_ids.mapped(
                lambda f: getattr(employee.sudo(), f.name).user_id
            )

        elif self.condition_type == "user":
            # determine applicable line
            if len(self.line_ids) == 1:
                line = self.line_ids
            else:
                line = max(
                    self.line_ids.filtered(
                        lambda l: data.get("currency_id").id in (l.currency_ids.ids if l.currency_ids else [])
                                  and l.amount is not None
                                  and l.amount <= data.get("amount")
                    ),
                    key=lambda l: l.amount or float("-inf"),
                    default=False,  # avoids ValueError if no match
                )
            if not line:
                return False

            users_dict[line.name] = line.user_ids if line else self.env["res.users"]

        elif self.condition_type == "optional":
            if data.get("optional_approver_id"):
                users_dict[self.name] = data.get("optional_approver_id")

        if not any(users_dict.values()) and self.condition_type == "user":
            raise UserError(
                _("No valid approver user found for condition: %s") % self.name
            )
        # return a dictionary of lists with user IDs
        for name, users in users_dict.items():
            return [
                {
                    "status": "new",
                    "condition_id": self.id,
                    "user_id": user.id,
                    "name": name,
                }
                for user in users
            ]


class ApprovalConditionLine(models.Model):
    """Approval condition line model holding user assignments and amount thresholds."""

    _name = "approval.condition.line"
    _description = "Approval Condition Line"

    name = fields.Char(string="Name", required=True)
    user_ids = fields.Many2many("res.users")
    amount = fields.Float("Amount")
    currency_ids = fields.Many2many("res.currency")
    condition_id = fields.Many2one("approval.condition")
    company_id = fields.Many2one(
        "res.company", "Company", related="condition_id.company_id"
    )
