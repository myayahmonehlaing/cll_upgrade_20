# Copyright 2004 Tiny SPRL
# Copyright 2016 Sodexis
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models , api


class Facility(models.Model):
    _name = "res.facility"
    _description = "Facility"

    name = fields.Char('Name')
    code = fields.Char('Code')


    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)


    @api.depends('name', 'code')
    def _compute_display_name(self):
        for facility in self.sudo():
            facility.display_name = f' [ {facility.code} ] {facility.name}'