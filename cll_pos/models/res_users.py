from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command


class Users(models.Model):
    """ User class. A res.users record models an OpenERP user and is different
        from an employee.

        res.users class now inherits from res.partner. The partner model is
        used to store the data related to the partner: lang, name, address,
        avatar, ... The user model is now dedicated to technical data.
    """
    _inherit = "res.users"

    pos_config_ids = fields.Many2many("pos.config")