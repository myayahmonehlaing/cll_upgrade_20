# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
from odoo import api,Command, fields, models, _
from odoo.tools import email_split, float_repr, float_round, is_html_empty
from markupsafe import Markup

class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    advance_id = fields.Many2one("account.move","Advance")
    number = fields.Char("Number",copy=False, readonly=True,)

    def action_sheet_move_create(self):
        res = super(HrExpenseSheet, self).action_sheet_move_create()

        for sheet in self:
            move = False
            if hasattr(sheet, 'account_move_id') and sheet.account_move_id:
                move = sheet.account_move_id
            elif hasattr(sheet, 'account_move_ids') and sheet.account_move_ids:
                move = sheet.account_move_ids[0]

            if move:
                for msg in sheet.sudo().message_ids.sorted('id'):
                    body_content = msg.body or ""

                    if msg.tracking_value_ids:
                        body_content += "<ul style='margin-bottom: 0px; font-size: 13px;'>"
                        for track in msg.tracking_value_ids:

                            # ပြောင်းလဲသွားသော Field နာမည်ကို ယူခြင်း
                            field_name = getattr(track, 'field_string', getattr(track, 'field_desc', ''))
                            if not field_name and hasattr(track, 'field_id') and track.field_id:
                                field_name = track.field_id.field_description
                            if not field_name:
                                field_name = 'Status / Field'

                            # အဟောင်း နှင့် အသစ် တန်ဖိုးများကို ယူခြင်း
                            old_val = str(
                                getattr(track, 'old_value_char', '') or getattr(track, 'old_value_text', '') or getattr(
                                    track, 'old_value_integer', '') or '')
                            new_val = str(
                                getattr(track, 'new_value_char', '') or getattr(track, 'new_value_text', '') or getattr(
                                    track, 'new_value_integer', '') or '')

                            body_content += f"<li><b>{field_name}</b>: {old_val} &#8594; {new_val}</li>"
                        body_content += "</ul>"

                    # စာသား (သို့) Tracking ရှိမှသာ ပို့မည်
                    if body_content:
                        author = msg.author_id.name if msg.author_id else "System"
                        final_body = f"<p><em style='color: #666;'>(Expense Log: {msg.date} by {author})</em></p> {body_content}"

                        move.message_post(
                            body=Markup(final_body),  # <--- ဒီနေရာလေး ပြင်လိုက်တာပါ (Markup ခံလိုက်ခြင်း)
                            subtype_xmlid='mail.mt_note'
                        )

        return res

    def get_tracking_values_for_report(self, msg):
        """XML Report မှ ခေါ်သုံးရန် Tracking Value များကို သပ်သပ်ရပ်ရပ် စီစဉ်ပေးသော Function"""
        tracks = []
        if msg.tracking_value_ids:
            for track in msg.tracking_value_ids:
                # Field Name ကို အမှားကင်းကင်း ရယူခြင်း
                field_name = track.field_id.field_description if track.field_id else 'Status'

                # အဟောင်း နှင့် အသစ် တန်ဖိုးများကို ရယူခြင်း
                old_val = str(
                    getattr(track, 'old_value_char', '') or getattr(track, 'old_value_text', '') or getattr(track,
                                                                                                            'old_value_integer',
                                                                                                            '') or '')
                new_val = str(
                    getattr(track, 'new_value_char', '') or getattr(track, 'new_value_text', '') or getattr(track,
                                                                                                            'new_value_integer',
                                                                                                            '') or '')

                tracks.append({
                    'field_name': field_name,
                    'old_val': old_val,
                    'new_val': new_val
                })
        return tracks

    def get_filtered_report_messages(self):
        """Report တွင် Submitted နောက်ပိုင်း Log များကိုသာ ဖမ်းယူပြသရန်"""
        self.ensure_one()
        # အဟောင်းဆုံးမှ အသစ်ဆုံးသို့ အရင်စီစဉ်ပါမည်
        messages = self.message_ids.sorted('id')

        first_submit_id = None
        for msg in messages:
            # ဤ message တွင် "Submitted" ဟူသော status ပါမပါ စစ်ဆေးခြင်း
            tracks = self.get_tracking_values_for_report(msg)
            for track in tracks:
                if 'Submit' in track['new_val']:  # 'Submitted' ဖြစ်သွားသော Log ကို ရှာတွေ့လျှင်
                    first_submit_id = msg.id
                    break
            if first_submit_id:
                break

        if first_submit_id:
            # "Submitted" ဖြစ်သွားသည့် Log နှင့် ၎င်းနောက်ပိုင်း (ID ကြီးသော) မှတ်တမ်းများကိုသာ ယူမည် (အစပိုင်း Log များ အလိုအလျောက် ပျောက်သွားပါမည်)
            valid_msgs = messages.filtered(lambda m: m.id >= first_submit_id)
        else:
            # အကယ်၍ ရှာမတွေ့ခဲ့ပါက ရှိသမျှအကုန် ပြန်ယူပါမည်
            valid_msgs = messages
        # Print ထုတ်ချိန်တွင် အသစ်ဆုံးကို အပေါ်ဆုံးထားရန် ပြောင်းပြန် (Reverse) ပြန်လှည့်ပေးမည်

        return valid_msgs.sorted('id', reverse=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            vals['number'] = self.env['ir.sequence'].next_by_code('hr.expense.sheet')

        return super().create(vals_list)

class HrExpense(models.Model):
    _inherit = "hr.expense"



