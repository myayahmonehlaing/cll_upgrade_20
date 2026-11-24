# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models,api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility", readonly=False
    )

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix

    # @api.depends('picking_type_id')
    # def _compute_facility_id(self):
    #     for order in self:
    #         if order.picking_type_id:
    #             order.facility_id =  order.picking_type_id.warehouse_id.facility_id.id


    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        if result.name and result.facility_id:
            result.name = result.facility_id.code + '/' + result.name
        return result

    def write(self, values):
        result = super().write(values)
        if self.state in ['draft','sent']  and 'facility_id' in values and self.facility_id:
            self.name = self.facility_id.code + '/' + self.name[5:len(self.name)]
        return result

    def _prepare_picking(self):
        result = super()._prepare_picking()
        if self.facility_id:
            result['facility_id'] = self.facility_id.id
        return result


    def _prepare_invoice(self):
        result = super()._prepare_invoice()
        if self.facility_id:
            result['facility_id'] = self.facility_id.id
        return result
