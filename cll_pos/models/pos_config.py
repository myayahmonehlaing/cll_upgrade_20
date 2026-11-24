# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _, Command


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _default_sale_journal_1(self):
        return self.env['account.journal'].search([
            *self.env['account.journal']._check_company_domain(self.env.company),
            ('type', 'in', ('sale', 'general')),
            ('code', '=', 'POSS'),
        ], limit=1)

    sale_journal_id = fields.Many2one(
        'account.journal', string='Sales Journal',
        domain=[('type', 'in', ('general', 'sale'))],
        check_company=True,
        help="Accounting journal used to post POS session journal entries and POS invoice payments.",
        default=_default_sale_journal_1,
        ondelete='restrict')




