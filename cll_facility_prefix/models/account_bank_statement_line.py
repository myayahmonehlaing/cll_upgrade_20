from odoo import api, Command, fields, models, _


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _synchronize_to_moves(self, changed_fields):
        super()._synchronize_to_moves(changed_fields)
        for line in self.filtered(lambda l: l.pos_session_id.facility_id):
            line.with_context(skip_account_move_synchronization=True).move_id.write({
                'facility_id': line.pos_session_id.facility_id.id,
            })