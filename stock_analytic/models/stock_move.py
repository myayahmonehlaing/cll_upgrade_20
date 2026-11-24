
from odoo import api, models


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "analytic.mixin"]

    def _get_account_move_line_vals(self):
        values = super()._get_account_move_line_vals()
        account = (self.location_id.valuation_account_id or self.location_dest_id.valuation_account_id )

        if not account or not self.analytic_distribution:
            return values

        for value in values:
            if value.get('account_id') == account.id:
                value['analytic_distribution'] = self.analytic_distribution

        return values


