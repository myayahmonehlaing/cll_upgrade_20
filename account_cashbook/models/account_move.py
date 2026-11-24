# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning



class AccountMove(models.Model):
    _inherit = "account.move"

    cashbook_id = fields.Many2one(
        comodel_name='account.cashbook',
        string='Cash Book',
        index=True,
        copy=False,
        check_company=True)


    def action_open_cashbook(self):
        self.ensure_one()

        return {
            'name': _("Cashbook"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'account.cashbook',
            'res_id': self.cashbook_id.id,
            'target': 'current',
        }
