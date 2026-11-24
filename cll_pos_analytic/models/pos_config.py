from odoo import api, fields, models


class PosConfig(models.Model):
    _name = "pos.config"
    _inherit = ["pos.config", "analytic.mixin"]
