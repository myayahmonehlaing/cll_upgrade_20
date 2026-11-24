"""Extend res.partner model to include additional fields."""

# pylint: disable=import-error,too-few-public-methods
from datetime import timedelta

from odoo import api, fields, models


class ResPartner(models.Model):
    """Extend res.partner model to include additional fields."""

    _inherit = "res.partner"

    # company_id = fields.Many2one(
    #     'res.company', 'Company',
    #      index=True,default=lambda self: self.env.company if self.env.company.id == 1 else False)

    is_customer = fields.Boolean(string="Is Customer")
    is_vendor = fields.Boolean(string="Is Vendor")
    is_employee = fields.Boolean(string="Is Employee")

    is_provider = fields.Boolean(
        string="Provider", help="Provider created by importing from Charm HR csv file"
    )
    is_refer = fields.Boolean(
        string="Refer", help="Refer created by importing from Charm HR csv file"
    )
    date_of_birth = fields.Date(string="Date of Birth")
    gender_id = fields.Selection(
        [
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
        ],
        string="Gender",
    )
    ref = fields.Char(string="Customer ID")
    age = fields.Char(string="Age", compute="_compute_age")
    fingerprint_id = fields.Char(
        compute="_compute_fingerprint_id", string="Fingerprint ID", store=True
    )
    partner_group_id = fields.Many2one("res.partner.group", string="Patient Category")

    @api.depends("employee_ids", "employee_ids.x_studio_fingerprint_id")
    def _compute_fingerprint_id(self):
        for partner in self:
            partner.fingerprint_id = (
                partner.employee_ids[0].x_studio_fingerprint_id
                if partner.employee_ids
                else False
            )

    def _compute_age(self):
        for partner in self:
            if partner.date_of_birth:
                today = fields.Date.context_today(self)
                birth_date = partner.date_of_birth

                # Check if birth_date is in the future
                if birth_date > today:
                    partner.age = "0 days"
                    continue

                # Calculate the difference in years, months, and days
                years = today.year - birth_date.year
                months = today.month - birth_date.month
                days = today.day - birth_date.day

                if days < 0:  # Handle negative day differences by adjusting months
                    months -= 1
                    # Get the last day of the previous month to add days correctly
                    last_day_of_prev_month = (
                        birth_date.replace(month=(birth_date.month % 12) + 1, day=1)
                        - timedelta(days=1)
                    ).day
                    days += last_day_of_prev_month

                if months < 0:  # Handle negative month differences by adjusting years
                    years -= 1
                    months += 12

                # Determine how to display the age
                if years > 0:
                    partner.age = f"{years} year{'s' if years > 1 else ''}"
                elif months > 0:
                    partner.age = f"{months} month{'s' if months > 1 else ''}"
                elif days >= 0:
                    partner.age = f"{days} day{'s' if days > 1 else ''}"
            else:
                partner.age = "0 days"
