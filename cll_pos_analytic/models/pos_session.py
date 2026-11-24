# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, _, api, fields, models

class PosSession(models.Model):
    _inherit = "pos.session"

    def _prepare_session_closing_extra_line_commands(self, orders, refund, payments=[]):
        lines = super()._prepare_session_closing_extra_line_commands(
            orders, refund, payments
        )
        if self.config_id.analytic_distribution:
            for line in lines:
                if line[0] == Command.CREATE and line[2]['quantity'] > 0:
                    line[2]['analytic_distribution'] = (
                        self.config_id.analytic_distribution
                    )

        return lines