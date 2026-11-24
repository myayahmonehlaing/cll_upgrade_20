from odoo import _, api, fields, models
from odoo.exceptions import UserError
from collections import defaultdict

class PosOrderProduct(models.TransientModel):
    _name = 'pos.order.product'
    _description = 'Choose number of products for order print'

    no_of_label = fields.Integer(string="Number of Labels")
    start_position = fields.Integer(string="Start Position")


    def _prepare_report_data(self):
        if self.no_of_label <= 0:
            raise UserError(_('You need to set a positive quantity for no of label.'))
        if self.start_position <= 0:
            raise UserError(_('You need to set a positive quantity for start position.'))

        xml_id = 'cll_pos.action_report_pos'

        data = {
            'no_of_label': int(self.no_of_label),
            'start_position': self.start_position,
            'wizard_id': self.id,
        }
        return xml_id, data


    def process(self):
        self.ensure_one()
        xml_id, data = self._prepare_report_data()
        if not xml_id:
            raise UserError(_('Unable to find report template for %s format', self.print_format))
        report_action = self.env.ref(xml_id).report_action(None, data=data, config=False)
        report_action.update({'close_on_report_download': True})
        return report_action