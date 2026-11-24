"""Extensions to Sale Order and Sale Order Line Models."""

# pylint: disable=import-error,too-few-public-methods,protected-access
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.addons.web.controllers import domain
from odoo.exceptions import ValidationError
from ..dataclasses.datamodels import InvoiceStatus, PartOfPackage, VisitType


class SaleOrder(models.Model):
    """Extension of Sale Order Model."""

    _inherit = "sale.order"

    ehr_invoice_status = fields.Selection(
        selection=InvoiceStatus.get_selection(), string="EHR Invoice Status", store=True
    )
    ehr_provider_id = fields.Many2one("ehr.provider", "Provider")
    visit_type = fields.Selection(selection=VisitType.get_selection())
    refer_specific = fields.Char(string="Refer Specific Source")
    partner_id = fields.Many2one("res.partner", domain="[('is_customer', '=', True)]")
    partner_group_id = fields.Many2one("res.partner.group", string="Patient Category")


    @api.constrains("name", "company_id")
    def _check_name_company_unique(self):
        for record in self:
            if not record.name:
                continue

            domain = [
                ("id", "!=", record.id),
                ("name", "=", record.name),
                ("company_id", "=", record.company_id.id),
            ]

            if self.search_count(domain):
                raise ValidationError(
                    _("This name is already used in this company : %s", record.name)
                )

    @api.onchange("partner_id")
    def _onchange_patient_category(self):
        if not self.env.context.get("from_import") and self.partner_id:
            self.partner_group_id = self.partner_id.partner_group_id

    def _prepare_confirmation_values(self):
        """Prepare the sales order confirmation values. Customize for MPTZ

        Note: self can contain multiple records.

        :return: Sales Order confirmation values
        :rtype: dict
        """
        return {
            "state": "sale",
        }

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        refer_id = self.order_line.mapped('refer_id')[:1]

        invoice_vals.update({
            # 'origin': self.origin, for upgrade temp
            'refer_id': refer_id.id if refer_id else False,
            'invoice_date': self.date_order + timedelta(hours=6, minutes=30) if self.date_order else False,
            'ehr_invoice_status': self.ehr_invoice_status,
            'partner_group_id': self.partner_group_id.id if self.partner_group_id else False,
        })

        return invoice_vals



class SaleOrderLine(models.Model):
    """Extension of Sale Order Line Model."""

    _inherit = "sale.order.line"

    lot_id = fields.Many2one("stock.lot", string="Batch No",  domain="[('product_id', '=', product_id)]" )
    expired_date = fields.Datetime(related="lot_id.expiration_date", store=True)
    discount_amount = fields.Char("Discount")
    provider_id = fields.Many2one(comodel_name="res.partner", string="Provider")
    refer_id = fields.Many2one(comodel_name="res.partner", string="Refer Doctor")
    is_product_part = fields.Selection(
        selection=PartOfPackage.get_selection(), string="Is Product Part of Package"
    )
    ehr_discount = fields.Float(string="Discount Amt.")


    @api.depends('product_uom_qty', 'discount','ehr_discount', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        super()._compute_amount()

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if self.ehr_discount:
            res["discount_amount"] = self.ehr_discount
        if self.refer_id:
            res.update({'refer_id': self.refer_id.id})
        return res

    def _purchase_service_prepare_order_values(self, supplierinfo):
        result = super()._purchase_service_prepare_order_values(supplierinfo)
        if self.order_id.client_order_ref:
            result['partner_ref'] = self.order_id.client_order_ref
        return result


class EhrProvider(models.Model):
    """EHR Provider Model."""

    _name = "ehr.provider"
    _description = "EHR Provider"

    name = fields.Char("Name")
