# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
class PosOrder(models.Model):
    _inherit = "pos.order"

    ref_id = fields.Many2one(comodel_name='res.partner', string="Refer Doctor")
    clinic_id = fields.Many2one(comodel_name='res.partner', string="Refer Clinic")

