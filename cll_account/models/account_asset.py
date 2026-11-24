from odoo import api,Command, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    model = fields.Char(string="Model")
    code = fields.Char(string="Asset Code")
    location_id = fields.Many2one("stock.location", compute = '_compute_location_id',inverse='_inverse_location_id'
                                  ,store=True,tracking=True)
    batch_number = fields.Char("Batch No.",tracking=True)



    @api.depends('original_move_line_ids')
    def _compute_location_id(self):
        for record in self:
            record.location_id = (
                record.original_move_line_ids[0].purchase_line_id.order_id.picking_type_id.default_location_dest_id.id
                if record.original_move_line_ids else False
            )

    def _inverse_location_id(self):
        return


    @api.constrains('company_id', 'code')
    def _constrains_code(self):
        # only consider records where code is set
        valid_records = self.filtered(lambda rec: rec.code)
        if not valid_records:
            return

        # check for duplicates in each root company
        by_root_company = self.grouped(lambda record: record.company_id.root_id)
        for root_company, records in by_root_company.items():
            by_code = records.grouped('code')
            if len(by_code) < len(records):
                # retrieve duplicates within self
                duplicates = next(recs for recs in by_code.values() if len(recs) > 1)
            else:
                # search for duplicates of self in database
                duplicates = self.search([
                    ('company_id', 'child_of', root_company.id),
                    ('code', 'in', list(by_code)),
                    ('id', 'not in', records.ids),
                ])
            if duplicates:
                raise ValidationError(
                    _("The code of the asset must be unique per company!")
                    + "\n" + "\n".join(f"- {duplicate.code} in {duplicate.company_id.name}" for duplicate in duplicates)
                )