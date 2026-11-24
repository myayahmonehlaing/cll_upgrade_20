from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError
from datetime import datetime

class ReportPOSOrderProductLabel(models.AbstractModel):
    _name = 'report.cll_pos.report_posorder_product_label'
    _description = 'POS Order Product Label'

    def _get_report_values(self, docids, data):
        pos_order = self.env['pos.order'].browse(data['context'].get('active_id'))
        return {
            'posorder': pos_order,
            'partner_id':pos_order.partner_id,
            'center':pos_order.picking_ids,
            'posorderline':pos_order.lines.filtered(lambda line:line.to_print),
            'no_of_label': data['no_of_label'],
            'start_position': data['start_position'],
            'report_date': datetime.today().strftime('%d-%m-%Y')
        }


