# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _, Command

class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )