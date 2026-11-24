# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models

class PosOrder(models.Model):
    _inherit = "pos.order"

    facility_id = fields.Many2one(related='config_id.facility_id',string="Facility",store=True)

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        if self.facility_id:
            vals.update({'facility_id': self.facility_id.id})
        return vals


class PosSession(models.Model):
    _inherit = "pos.session"

    facility_id = fields.Many2one(related='config_id.facility_id', string="Facility", store=True)

    def _prepare_session_move_vals(self, orders):
        res = super()._prepare_session_move_vals(orders)
        if self.facility_id:
            res.update({'facility_id': self.facility_id.id})
        return res


class PosConfig(models.Model):
    _inherit = "pos.config"

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )