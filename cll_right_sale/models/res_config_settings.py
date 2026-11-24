# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    right_sale = fields.Boolean(
        string="Custom Configuration",
        related='company_id.right_sale',
        readonly=False,
        store=True
    )
    right_deferred_journal_id = fields.Many2one(
        'account.journal', string='Deferred Journal',
        domain=[('type', 'in', ('general', 'sale'))],
        related='company_id.right_deferred_journal_id',
        check_company=True,
        readonly=False,
        help="Accounting journal used to generate deferred entries when delivery order is done",
        ondelete='restrict')


