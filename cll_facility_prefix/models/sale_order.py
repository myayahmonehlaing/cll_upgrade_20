# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models,api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    facility_id = fields.Many2one(
        comodel_name='res.facility',
        string="Facility",
    )

    use_facility = fields.Boolean(compute='_compute_use_facility')

    @api.depends('company_id')
    def _compute_use_facility(self):
        for record in self:
            record.use_facility = record.company_id.use_facility_code_to_determine_prefix


    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.facility_id = self.warehouse_id.facility_id.id

    # @api.model_create_multi
    # def create(self, vals_list):
    #     result = super().create(vals_list)
    #     if result.name and result.facility_id:
    #         result.name = result.facility_id.code + '/' + result.name
    #     return result
    #
    # def write(self, values):
    #     result = super().write(values)
    #     if 'facility_id' in values and self.facility_id:
    #         self.name = self.facility_id.code + '/' + self.name[5:len(self.name)]
    #     return result

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.facility_id:
            invoice_vals.update({
                'facility_id': self.facility_id.id,
            })
        return invoice_vals



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _purchase_service_prepare_order_values(self, supplierinfo):
        result = super()._purchase_service_prepare_order_values(supplierinfo)
        if self.order_id.facility_id:
            result['facility_id'] = self.order_id.facility_id.id
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'),
                 ('warehouse_id.facility_id', '=',  self.order_id.facility_id.id),
                 ('warehouse_id.company_id', '=', self.env.context.get('company_id') or self.env.company.id)], limit=1)
            if picking_type:
                result['picking_type_id']= picking_type.id
        gender = self.order_id.partner_id.gender_id.title() if self.order_id.partner_id.gender_id else ''
        result['partner_ref'] =  f"{ self.order_id.partner_id.ref if self.order_id.partner_id.ref else ' ' } - {self.order_id.partner_id.name} { gender } {self.order_id.partner_id.age} "
        result['refer_specific'] = self.order_id.refer_specific
        return result

    def _purchase_service_match_purchase_order(self, partner, company=False):
        domain = [
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft'),
            ('company_id', '=', (company and company or self.env.company).id),
            ('origin','=',self.order_id.name)
        ]
        if self.env.context.get('facility_id'):
            domain.append(['facility_id', '=', self.env.context.get('facility_id').id])

        return self.env['purchase.order'].search(domain, order='id desc')

    def _match_or_create_purchase_order(self, supplierinfo):
        purchase_order = self._purchase_service_match_purchase_order(supplierinfo.partner_id)[:1]
        # if not purchase_order:
        if self.product_id.product_tmpl_id.service_tracking == 'subcontract' and not purchase_order:
            purchase_order = self._create_purchase_order(supplierinfo)
        return purchase_order

    def _purchase_service_create(self, quantity=False):
        """ On Sales Order confirmation, some lines (services ones) can create a purchase order line and maybe a purchase order.
            If a line should create a RFQ, it will check for existing PO. If no one is find, the SO line will create one, then adds
            a new PO line. The created purchase order line will be linked to the SO line.
            :param quantity: the quantity to force on the PO line, expressed in SO line UoM
        """
        supplier_po_map = {}
        sale_line_purchase_map = {}

        for line in self:
            line = line.with_company(line._purchase_service_get_company())
            supplierinfo = line._purchase_service_match_supplier()
            partner_supplier = supplierinfo.partner_id

            # determine (or create) PO
            purchase_order = supplier_po_map.get(partner_supplier.id)
            if not purchase_order:
                purchase_order = line.with_context(facility_id=line.order_id.facility_id)._match_or_create_purchase_order(supplierinfo)
            so_name = line.order_id.name
            origins = (purchase_order.origin or '').split(', ')
            if so_name not in origins:
                purchase_order.write({'origin': ', '.join(origins + [so_name])})
            supplier_po_map[partner_supplier.id] = purchase_order

            # add a PO line to the PO
            values = line._purchase_service_prepare_line_values(purchase_order, quantity=quantity)
            purchase_line = line.env['purchase.order.line'].create(values)

            # link the generated purchase to the SO line
            sale_line_purchase_map.setdefault(line, line.env['purchase.order.line'])
            sale_line_purchase_map[line] |= purchase_line
        return sale_line_purchase_map

    def _purchase_service_generation(self):
        """ Create a Purchase for the first time from the sale line. If the SO line already created a PO, it
            will not create a second one.
        """
        sale_line_purchase_map = {}
        for line in self:
            line = line.with_company(line._purchase_service_get_company())
            # Do not regenerate PO line if the SO line has already created one in the past (SO cancel/reconfirmation case)
            if line.product_id.service_tracking == 'subcontract' and not line.purchase_line_count:
                result = line.with_context(facility_id=line.order_id.facility_id)._purchase_service_create()
                sale_line_purchase_map.update(result)
        return sale_line_purchase_map