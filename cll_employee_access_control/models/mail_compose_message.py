# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _action_send_mail(self, auto_commit=False):
        """Override to handle user request notification marking"""
        res = super(MailComposeMessage, self)._action_send_mail(auto_commit=auto_commit)

        # Check if we should mark the user request as notified
        if self._context.get('mark_user_request_as_notified'):
            model = self._context.get('default_model')
            res_id = self._context.get('default_res_ids')[0] if self._context.get('default_res_ids') else None
            
            if model == 'employee.access.control' and res_id:
                request = self.env['employee.access.control'].sudo().browse(res_id)
                # Update state immediately
                request.sudo().write({
                    'state': 'vendor_action',
                })
                request.message_post(
                    body=_("Admin notification email sent on %s") % fields.Datetime.now(),
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
        
        return res
