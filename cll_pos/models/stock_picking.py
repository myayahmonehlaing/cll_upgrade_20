# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta, datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _default_picking_type_id(self):
        picking_type_code = self.env.context.get('restricted_picking_type_code')
        if picking_type_code:
            picking_types = self.env['stock.picking.type'].search([
                ('code', '=', picking_type_code),
                ('company_id', '=', self.env.company.id),
            ])
            return picking_types[:1].id


    transfer_status = fields.Selection([
        ('draft','Draft'),
        ('done', 'Done'),
    ], default='draft',string='Transfer Status' )
    transfer_picking = fields.Boolean(string='Transfer Picking',default=False)
    available_picking_type_ids = fields.Many2many('stock.picking.type', compute='_compute_available_picking_type_ids')
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, readonly=True,check_company=True, default=_default_picking_type_id,
        domain="[('id', 'in', available_picking_type_ids)]")

    @api.depends('transfer_picking')
    def _compute_available_picking_type_ids(self):
        for picking_type in self:
            domain = []
            if picking_type.transfer_picking :
                domain=[('code', '=','outgoing'),('sequence_code', '=','POS')]
            picking_type.available_picking_type_ids = self.env['stock.picking.type'].search(domain).ids


    def action_transfer_done(self):
        self.write({'transfer_status':'done'})



    def _cron_set_done_pickings(self, date=None, day=5):
        request_date = fields.Date.context_today(self) if not date else date

        # Calculate the date 5 days before the request date
        five_days_ago = (
            datetime.strptime(request_date, "%Y-%m-%d").date()
            if isinstance(request_date, str)
            else request_date
        ) - timedelta(days=day)

        pickings = self.with_user(SUPERUSER_ID).search(
            [("scheduled_date", "<=", five_days_ago),("picking_type_id.code", "=", "outgoing")]
        )

        for picking in pickings.filtered(lambda p: p.state == 'assigned'):
            _logger.info("Schedule Action Picking ID to done : %s (%s)"%(picking.id, picking.name))
            try:
                picking._pre_action_done_hook()
                picking.with_context(cancel_backorder=False)._action_done()
                _logger.info("Done Picking ID : %s (%s)"%(picking.id, picking.name))
            except (UserError, ValidationError):
                pass


