# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models,api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix


    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        pickings = super()._create_picking_from_pos_order_lines(location_dest_id, lines, picking_type, partner)
        facility_id = lines.mapped('order_id.facility_id')
        if facility_id:
            pickings.write({'facility_id': facility_id.id})
        return pickings


    # @api.model_create_multi
    # def create(self, vals_list):
    #     pickings = super().create(vals_list)
    #     if pickings.name and pickings.facility_id:
    #         pickings.name = pickings.facility_id.code + '/' + pickings.name
    #     return pickings
    #
    # def write(self, values):
    #     result = super().write(values)
    #     if 'facility_id' in values and self.facility_id:
    #         self.name = self.facility_id.code + '/' + self.name[5:len(self.name)]
    #     return result


class StockMove(models.Model):
    _inherit = 'stock.move'


    def _get_facility_from_picking(self):
        return self.picking_id.facility_id.id or self.env.context.get('facility')

    def _get_new_picking_values(self):
        result = super()._get_new_picking_values()
        facility_id = self.sale_line_id.order_id.facility_id if self.sale_line_id and self.sale_line_id.order_id.facility_id  else False
        if facility_id:
            result['facility_id'] = facility_id.id
        return result

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        result = super()._prepare_account_move_vals( credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
        if self.picking_id.facility_id or self.env.context.get('facility') :
            result['facility_id'] = self._get_facility_from_picking()
        return result