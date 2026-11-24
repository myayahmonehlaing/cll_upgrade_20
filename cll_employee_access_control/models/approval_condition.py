"""
Approval Rules and Conditions

This module defines the models and logic for configuring approval rules,
conditions, and approvers within Odoo. It supports multiple types of conditions
(field-based, user-based, or optional), amount thresholds, and company-specific
rules.
"""

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api,fields, models
from odoo.exceptions import UserError


class ApprovalConditon(models.Model):
    """Defines the conditions used within an approval rule."""

    _inherit = "approval.condition"

    user_type = fields.Selection(
        selection=[('light', 'Light User'), ('standard', 'Standard User')], string='User Type'
    )
    model_id = fields.Many2one(
        "ir.model",store=True,related='rule_id.model_id',)
    hide_user_type = fields.Boolean(string="Hide User Type",compute="_compute_hide_user_type")

    @api.depends('rule_id.model_id')
    def _compute_hide_user_type(self):
        for condition in self:
            condition.hide_user_type = ( condition.model_id.model != 'employee.access.control')
