# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    right_sale = fields.Boolean(string="Right Sale", default=False)
    right_deferred_journal_id = fields.Many2one(
        'account.journal', string='Deferred Journal',)