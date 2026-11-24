"""
Approval Rules and Conditions

This module defines the models and logic for configuring approval rules,
conditions, and approvers within Odoo. It supports multiple types of conditions
(field-based, user-based, or optional), amount thresholds, and company-specific
rules.
"""

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ApprovalRule(models.Model):
    """Model for defining approval rules linked to specific models."""

    _name = "approval.rule"
    _description = "Approval Rule"
    _check_company_auto = True

    name = fields.Char(string="Name", required=True)
    model_id = fields.Many2one(
        "ir.model",
        required=True,
        ondelete="cascade",
    )
    condition_ids = fields.One2many(
        "approval.condition",
        "rule_id",
        string="Approval Lines",
        copy=True,
    )
    company_id = fields.Many2one(
        "res.company", "Company", required=True, default=lambda self: self.env.company
    )
