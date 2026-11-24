# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tools import float_compare, groupby
from odoo import api, fields, models, tools, _

class ProductProduct(models.Model):
    _inherit = "res.partner"

    def _get_ref_by_company(self):
        return [
            (company_id, [p.ref for p in partners if p.ref])
            for company_id, partners in groupby(self, lambda p: p.company_id.id)
        ]

    @api.constrains('ref')
    def _check_ref_uniqueness(self):
        """ With GS1 nomenclature, products and packagings use the same pattern. Therefore, we need
        to ensure the uniqueness between partners' ref and packagings' ones"""
        # Ref should only be unique within a company
        for company_id, ref_within_company in self._get_ref_by_company():
            self._check_duplicated_partner_ref(ref_within_company, company_id)

    def _get_ref_search_domain(self, ref_within_company, company_id):
        domain = [('ref', 'in', ref_within_company)]
        if company_id:
            domain.append(('company_id', 'in', (False, company_id)))
        return domain

    def _check_duplicated_partner_ref(self, ref_within_company, company_id):
        domain = self._get_ref_search_domain(ref_within_company, company_id)
        partners_by_ref = self.sudo()._read_group(
            domain, ['ref'], ['id:recordset'], having=[('__count', '>', 1)],
        )
        duplicates_as_str = "\n".join(
            self.env._(
                "- Ref \"%(ref)s\" already assigned to partner(s): %(partner_list)s",
                ref=ref, partner_list=duplicate_partners._filtered_access('read').mapped('display_name'),
            )
            for ref, duplicate_partners in partners_by_ref
        )
        if duplicates_as_str.strip():
            duplicates_as_str += _(
                "\n\nNote: partners that you don't have access to will not be shown above."
            )
            raise ValidationError(_("Ref(s) already assigned:\n\n%s", duplicates_as_str))