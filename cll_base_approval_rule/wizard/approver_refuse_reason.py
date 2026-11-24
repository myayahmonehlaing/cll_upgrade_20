# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ApprovalApproverRefuseWizard(models.TransientModel):
    """This wizard can be launched from an he.expense (an expense line)
    or from an hr.expense.sheet (En expense report)
    'hr_expense_refuse_model' must be passed in the context to differentiate
    the right model to use.
    """

    _name = "approval.approver.refuse.wizard"
    _description = "Approval Refuse Reason Wizard"

    reason = fields.Char(string="Reason", required=True)
    model_name = fields.Char(
        string="Model", help="Name of the model associated with this approval"
    )

    record_id = fields.Many2oneReference(
        model_field="model_name",
        help="Reference to the record in the model",
    )

    @api.model
    def default_get(self, fields): #pylint: disable=redefined-outer-name
        """Overwrite in order to get active_id to refuse with record ID"""
        res = super(ApprovalApproverRefuseWizard, self).default_get(fields)
        active_ids = self.env.context.get("active_ids", [])
        res.update(
            {
                "record_id": active_ids[0] if active_ids else False,
                "model_name": self.env.context.get("active_model"),
            }
        )
        return res

    def action_approval_refuse(self):
        """Funtion to refuse approval approver state with provided record ID browse by model name."""
        self.ensure_one()
        if self.model_name and self.record_id:
            record_id = self.env[self.model_name].sudo().browse(self.record_id)
            record_id.do_refuse(self.reason)
        return {"type": "ir.actions.act_window_close"}
