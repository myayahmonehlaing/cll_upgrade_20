from odoo import api, models, fields, _
from odoo.fields import Domain

class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.model
    def name_search(self, name="", domain=None, operator="ilike", limit=100,):
        domain = list(domain or [])

        if (
            self.env.context.get("analytic_groupby_plan_name")
            and self.env.company.show_plan_analytic_filter
        ):
            if name:
                domain = Domain.AND([
                    domain,
                    [("name", operator, name)],
                ])

            records = self.search(domain, limit=limit)

            return [
                (
                    record.id,
                    f"{record.name} ({record.plan_id.sudo().complete_name})"
                    if record.plan_id
                    else record.name,
                )
                for record in records
            ]

        return super().name_search(
            name=name,
            domain=domain,
            operator=operator,
            limit=limit,
        )