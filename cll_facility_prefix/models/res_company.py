# Copyright 2004 Tiny SPRL
# Copyright 2016 Sodexis
# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    use_facility_code_to_determine_prefix = fields.Boolean(
        string="Use facility to determine the prefix",
        help="Use facility to determine the prefix "
        "if the category has no settings for the prefix.",
    )
