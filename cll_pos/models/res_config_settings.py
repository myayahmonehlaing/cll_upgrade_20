# -*- coding: utf-8 -*-

from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    sale_journal_id = fields.Many2one(related='pos_config_id.sale_journal_id', readonly=False, string="Sales Journal")




class ResCompany(models.Model):
    _inherit = 'res.company'

