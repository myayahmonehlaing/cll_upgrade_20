"""Model for Patient Category."""

# pylint: disable=import-error,too-few-public-methods
from odoo import fields, models


class ResPartnerGroup(models.Model):
    """Model for Patient Category."""

    _name = "res.partner.group"
    _description = "Patient Category"

    name = fields.Char(string="Name")
