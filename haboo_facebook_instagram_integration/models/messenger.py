from odoo import models, fields, api, _
import requests
import json
from datetime import datetime, timedelta
import mimetypes
import base64
from odoo.exceptions import ValidationError,UserError
from datetime import datetime ,date, timedelta
import io

image_type = [
    "image/avif",
    "image/bmp",
    "image/gif",
    "image/vnd.microsoft.icon",
    "image/jpeg",
    "image/png",
    "image/svg+xml",
    "image/tiff",
    "image/webp",
]
document_type = [
    "application/xhtml+xml",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/xml",
    "application/vnd.mozilla.xul+xml",
    "application/zip",
    "application/x-7z-compressed",
    "application/x-abiword",
    "application/x-freearc",
    "application/vnd.amazon.ebook",
    "application/octet-stream",
    "application/x-bzip",
    "application/x-bzip2",
    "application/x-cdf",
    "application/x-csh",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-fontobject",
    "application/epub+zip",
    "application/gzip",
    "application/java-archive",
    "application/json",
    "application/ld+json",
    "application/vnd.apple.installer+xml",
    "application/vnd.oasis.opendocument.presentation",
    "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.oasis.opendocument.text",
    "application/ogg",
    "application/pdf",
    "application/x-httpd-php",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.rar",
    "application/rtf",
    "application/x-sh",
    "application/x-tar",
    "application/vnd.visio",
]
audio_type = [
    "audio/aac",
    "audio/midi",
    "audio/x-midi",
    "audio/mpeg",
    "audio/ogg",
    "audio/opus",
    "audio/wav",
    "audio/webm",
    "audio/3gpp",
    "audio/3gpp2",
]
video_type = [
    "video/x-msvideo",
    "video/mp4",
    "video/mpeg",
    "video/ogg",
    "video/mp2t",
    "video/webm",
    "video/3gpp",
    "video/3gpp2",
]

class MessengerSession(models.Model):
    _name = 'messenger.session'
    _description = 'Messanger Session'
    _rec_name = 'session_id'
    _order = "date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    session_id = fields.Char(string='Session ID')
    date = fields.Datetime(string='Date', default=fields.Datetime.now())
    customer_number = fields.Char(string='Customer Number')
    last_massage_datetime = fields.Datetime(compute="_compute_last_massage_datetime", string="Last Message", store=True)
    is_close_visible = fields.Boolean(compute="_compute_is_close_visible", search="_search_is_close_visible")
    agent_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Agent')
    send_message = fields.Text(string='Send Message')
    state = fields.Selection([('new', 'New'), ('running', 'Running'),
		('close', 'Closed')], default="new")
    product_image = fields.Binary('Image', attachment=True, help="filed to store image")
    file_name = fields.Char(string="File Name")
    messenger_messages_ids = fields.One2many("messenger.messages", 'session_id')

    provider_id = fields.Many2one('provider', string="Provider")
    partner_id = fields.Many2one('res.partner', string="Customer")
    customer_name = fields.Char(string='Customer Name', related="partner_id.name")
    instagram_account_id = fields.Char(related="partner_id.instagram_account_id")
    messenger_account_id = fields.Char(related="partner_id.messenger_account_id")
    company_id = fields.Many2one("res.company", string="Company")
    message = fields.Char(string='Message')
    sender_id = fields.Char(string="Sender id")

    def reopen_session(self):
        for record in self:
            existing_session = self.search([
                ('partner_id', '=', record.partner_id.id),
                ('state', 'in', ['running', 'new']), 
                ('id', '!=', record.id)  
            ], limit=1)

            if existing_session:
                raise ValidationError(f"The customer contact number already has an active session.")

            record.state = 'new'

    @api.depends("message_ids")
    def _compute_last_massage_datetime(self):
        for session in self:
            if session.message_ids:
                message = session.message_ids[0]
                session.last_massage_datetime = message.date
            else:
                session.last_massage_datetime = fields.Datetime.today()

    def _compute_is_close_visible(self):
        max_minute = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.auto_close_minute', 20)
        # print(max_minute, type(max_minute))
        for session in self:
            session_visible = False
            if session.last_massage_datetime:
                diff_date = datetime.now()- session.last_massage_datetime
                minutes = diff_date.total_seconds() / 60.0
                if minutes > int(max_minute):
                    session_visible = True
            session.is_close_visible = session_visible

    def close_whatsapp_session(self):
        sessions = self.search([('is_close_visible', '=', True), ('state', '=', 'running')])
        if sessions:
            sessions.write({'state': 'close'})
        return True

    def close_session(self):
        self.state = 'close'

    def start_session(self):
        self.state = 'running'
        self.agent_user_id = self.env.user

    def _search_is_close_visible(self, operator, value):
        if operator not in ['=', '!='] or not isinstance(value, bool):
            raise UserError(_('Operation not supported'))
        before_20 = datetime.now() - timedelta(hours=0, minutes=20)
        result_query = self.env['tata.whatsapp.session']._search([('last_massage_datetime', '<', before_20)])
        if (operator == '!=' and value is True) or (operator == '=' and value is False):
            domain_operator = 'not in'
        else:
            domain_operator = 'in'
        return [('id', domain_operator, result_query)]

    def create_opportunity_wizard(self):
        existing_opportunities = False
        # partner = self.env['res.partner'].search([('phone', '=', self.customer_number)], limit=1)
        if self.partner_id:
            existing_opportunities = self.env['crm.lead'].search([('partner_id', '=', self.partner_id.id)])
        self.state = 'close'    
        return {
            'name': 'Convert to Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'opportunity.convert.session.wizard',
            'view_mode': 'form',
            'context': {
                'default_session_id': self.id,
                'default_conversion_action': 'merge' if existing_opportunities else 'convert',
                'default_user_id': self.env.user.id,
                'default_partner_action': 'exist' if self.partner_id else 'create',
                'default_partner_id': self.partner_id.id if self.partner_id.id else False,
                'default_opportunity_ids': existing_opportunities.ids if existing_opportunities else False,
            },
            'target': 'new',
        }

    def action_view_opportunity(self):
        return {
            'name': 'Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list,form',
            'domain': [('session_id', '=', self.id)],
        }

    def action_send_message(self):
        if self.provider_id:
            if self.provider_id.meta_platform == 'instagram':
                self.provider_id.graph_api_instagram_send_message(self.partner_id, self.send_message, quotedMsgId=False)
            elif self.provider_id.meta_platform == 'facebook':
                self.provider_id.messenger_send_message(self.partner_id, self.send_message, quotedMsgId=False)

    def action_send_message_controller(self, message_body):
        print("action_send_message_controller ", message_body)
        if self.provider_id.meta_platform == 'instagram':
            result = self.provider_id.graph_api_instagram_send_message(self.partner_id, message_body, quotedMsgId=False)
        elif self.provider_id.meta_platform == 'facebook':
            result = self.provider_id.messenger_send_message(self.partner_id, message_body, quotedMsgId=False)
        return result

    def get_meta_attachment_type(self, mimetype):
        if mimetype in image_type:
            return "image"
        elif mimetype in video_type:
            return "video"
        elif mimetype in audio_type:
            return "audio"
        elif mimetype in document_type:
            return "file"
        return "file"

    def send_attachment_using_url_controller(self, attachments):
        attachment_ids = self.env['ir.attachment'].browse(attachments)
        page_id = self.provider_id.account_id
        access_token = self.provider_id.graph_api_token
        url = f"https://graph.{self.provider_id.meta_platform}.com/v24.0/{page_id}/message_attachments"

        results = []

        for attachment in attachment_ids:
            # print("\n attachment===========", attachment)
            file_data = base64.b64decode(attachment.datas)
            file_tuple = (attachment.name, file_data, attachment.mimetype)
            attachment_mimetype = self.get_meta_attachment_type(attachment.mimetype)

            inner_message = {
                "attachment": {
                    "type": attachment_mimetype,
                    "payload": {
                        "is_reusable": True
                    }
                }
            }
            payload = {
                'message': json.dumps(inner_message)
            }
            headers = {
                'Authorization': f'Bearer {access_token}',
            }

            try:
                response = requests.post(url, data=payload, files={'filedata': file_tuple}, headers=headers)
                result = response.json()
                # print("\nresult=======", result)

                if 'attachment_id' in result:
                    attachment_id_fb = result['attachment_id']

                    if self.provider_id.meta_platform == 'facebook':
                        answer = self.provider_id.messenger_send_media(
                            attachment_id_fb,
                            self.partner_id,
                            attachment_mimetype,
                        )
                    elif self.provider_id.meta_platform == 'instagram':
                        answer = self.provider_id.instagram_send_media(
                            attachment_id_fb,
                            self.partner_id,
                            attachment_mimetype,
                        )

                    # print("answer=============", answer)
                    results.append(answer)
                else:
                    print("No attachment_id in response:", result)

            except Exception as e:
                print("Failed to upload or decode response:", e)
                print("Raw response:", response.text)
                results.append({'error': str(e)})

        return results
            
class MessengerMessages(models.Model):
    _name = 'messenger.messages'
    _description = 'Messanger Messages'

    session_id = fields.Many2one('messenger.session', string='Session')
    message_text = fields.Text(string='Message')
    message_id = fields.Char(string='Message ID')
    attachment_ids = fields.Many2many(
        "ir.attachment", string="Attachments", readonly=True
    )
    
class CrmLead(models.Model):
    _inherit = 'crm.lead'

    session_id = fields.Many2one('messenger.session', string='Whatsapp Session')


    def view_session(self):
        session_id = self.env['messenger.session'].search([]).filtered(lambda x: x.opportunity_id.id == self.id)
        print("-----------", session_id,"-----session_id------\n")
        return {
            'name': 'Messanger Session',
            'type': 'ir.actions.act_window',
            'res_model': 'messenger.session',
            'view_mode': 'list,form',
            'domain': [('id', 'in',session_id.ids if session_id else [])],
            'context': {
                'create': False,
                'delete': False,
            }
        }

    def new_session(self):
        if (self.partner_id and self.partner_id.phone) or self.phone:
            self.session_id = self.env['messenger.session'].sudo().create({'opportunity_id': self.id, 'customer_name': self.partner_id.name, 'customer_number': self.partner_id.phone, 'session_id': self.name})
            return {
                'name': 'Messanger Session',
                'type': 'ir.actions.act_window',
                'res_model': 'messenger.session',
                'view_mode': 'form',
                'res_id': self.session_id.id,
                'context': {
                    'create': False,
                    'delete': False,
                }
            }
        return True