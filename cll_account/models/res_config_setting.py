# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Company(models.Model):
    _inherit = 'res.company'

    show_plan_analytic_filter = fields.Boolean('Show Plan Analytic Filter', default=False)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_plan_analytic_filter = fields.Boolean(related='company_id.show_plan_analytic_filter', string='Show Plan Analytic Filter', readonly=False)




