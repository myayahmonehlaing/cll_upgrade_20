# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Company(models.Model):
    _inherit = 'res.company'

    advance_approval = fields.Boolean(string='Employee Advance Approval')
    bill_approval = fields.Boolean(string='Bill Approval')
    vendor_advance_approval = fields.Boolean(string='Vendor Advance Approval')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    advance_approval = fields.Boolean(related='company_id.advance_approval',
                                            string='Employee Advance Approval', readonly=False)
    bill_approval = fields.Boolean(related='company_id.bill_approval',
                                      string='Bill Approval', readonly=False)
    vendor_advance_approval = fields.Boolean(related='company_id.vendor_advance_approval',
                                   string='Vendor Advance Approval', readonly=False)




