from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_move_line_vals_from_base_line(self,base_line):
        line_vals = super()._prepare_move_line_vals_from_base_line(base_line)
        if self.config_id.analytic_distribution:
            line_vals.update({
                'analytic_distribution':self.config_id.analytic_distribution
            })
        return line_vals


