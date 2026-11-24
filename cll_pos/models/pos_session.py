# -*- coding: utf-8 -*-

from odoo import api, models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _validate_session(
        self,
        balancing_account=False,
        amount_to_balance=0,
        bank_payment_method_diffs=None,
    ):
        res = super()._validate_session(
            balancing_account, amount_to_balance, bank_payment_method_diffs
        )
        for order in (
            self.env["pos.order"].sudo().browse([o["id"] for o in self.order_ids])
        ):
            if order.state == "done":
                for line in order.lines:
                    line._purchase_service_generation()
                    # line.purchase_line_ids.order_id.button_confirm()
        return res

    # @api.model
    # def _pos_ui_models_to_load(self):
    #     res = super()._pos_ui_models_to_load()
    #     res.extend(['res.partner.title','res.partner.company'])
    #     return res

    # def _get_pos_ui_res_partner_title(self, params):
    #     return self.env['res.partner.title'].search_read(**params['search_params'])

    # def _get_pos_ui_res_partner_company(self, params):
    #     return self.env['res.partner'].search_read(**params['search_params'])

    # def _loader_params_res_partner_title(self):
    #     return {'search_params': {'domain': [], 'fields': ['id','name']}}

    # def _loader_params_res_partner_company(self):
    #     return {'search_params': {'domain': [('is_company', '=', True)], 'fields': ['id','name']}}

    # def _loader_params_res_partner(self):
    #     vals = super()._loader_params_res_partner()
    #     vals['search_params']['fields'] += ['title', 'date_of_birth', 'parent_id', 'gender_id', 'age']
    #     return vals
6
