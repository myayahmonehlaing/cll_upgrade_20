from odoo import models, fields, api


class AccountReport(models.AbstractModel):
    _inherit = "account.report"

    def _create_column_analytic(self, options):
        super()._create_column_analytic(options)

        if not self.env.company.show_plan_analytic_filter:
            return

        accounts = self.env["account.analytic.account"].browse(
            options.get("analytic_accounts_groupby")
        )

        if not accounts or not options.get("column_headers"):
            return

        analytic_headers = options["column_headers"][-1]

        for header in analytic_headers:
            forced_options = header.get("forced_options", {})
            account_ids = forced_options.get("analytic_accounts_list")

            if not account_ids or len(account_ids) != 1:
                continue

            account = accounts.filtered(
                lambda a: a.id == account_ids[0]
            )

            if account and account.plan_id:
                header["name"] = (
                    f"{account.name} "
                    f"({account.plan_id.sudo().complete_name})"
                )