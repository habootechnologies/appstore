from odoo import models, fields, api,_
import requests
import json
from datetime import datetime, timedelta
import mimetypes
import base64
from odoo.exceptions import ValidationError,UserError

class TataWhatsappSession2(models.Model):
    _name = 'tata.whatsapp.session.2'
    _description = 'Whatsapp Session 2'
    _rec_name = 'session_id'
    _order = "date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    session_id = fields.Char(string='Session ID')
    date = fields.Datetime(string='Date', default=fields.Datetime.now())
    customer_name = fields.Char(string='Customer Name',required=True)
    customer_number = fields.Char(string='Customer Number',required=True)
    last_massage_datetime = fields.Datetime(compute="_compute_last_massage_datetime", string="Last Message", store=True)
    is_close_visible = fields.Boolean(compute="_compute_is_close_visible", search="_search_is_close_visible")
    agent_user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Agent')
    send_message = fields.Text(string='Send Message')
    sess_id = fields.Char(string='ID')
    state = fields.Selection([('new', 'New'), ('running', 'Running'),
		('close', 'Closed')], default="new",compute='_compute_state',store=True)
    product_image = fields.Binary('Image', attachment=True, help="filed to store image")
    file_name = fields.Char(string="File Name")
    is_gen_con = fields.Boolean("General Conversation")
    remarks = fields.Text()
    new_opporunity = fields.Boolean()
    running_date = fields.Datetime(string='Running Date')

    def new_send_whatsapp_message_2(self):
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        if not access_token:
            raise ValidationError("Enter Session token first")
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
            "Content-Type": 'application/json',
        }
        data = {
            "to": self.customer_number,
            "type": "template",
            "source": "external",
            "template": {
                "name": "navaratrigoluoffercode120925",
                "language": {
                    "code": "en"
                },
                "components": [

                ]
            }
        }
        response = requests.post(url=url, headers=headers, json=data)
        response_json = json.loads(response.text)


    def new_send_whatsapp_message_shopify_2(self):
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        if not access_token:
            raise ValidationError("Enter Session token first")
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
            "Content-Type": 'application/json',
        }
        data = {
            "to": self.customer_number,
            "type": "template",
            "source": "external",
            "template": {
                "name": "abandoned_cart_enquiry_",
                "language": {
                    "code": "en"
                },
                "components": []
            }
        }
        response = requests.post(url=url, headers=headers, json=data)
        print('########## response.status_code ###############', response.status_code)
        response_json = json.loads(response.text)


    @api.depends('is_gen_con')
    def _compute_state(self):
        for record in self:
            if record.is_gen_con:
                record.state = 'close'

    def reopen_session(self):
        for record in self:
            existing_session = self.search([
                ('customer_number', '=', record.customer_number),
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
        max_minute = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.auto_close_minute_2', 20)
        for session in self:
            session_visible = False
            if session.last_massage_datetime:
                diff_date = datetime.now()- session.last_massage_datetime
                minutes = diff_date.total_seconds() / 60.0
                if minutes > int(max_minute):
                    session_visible = True
            session.is_close_visible = session_visible

    def close_whatsapp_session_2(self):
        sessions = self.search([('is_close_visible', '=', True), ('state', '=', 'running')])
        if sessions:
            sessions.write({'state': 'close'})
        return True

    def close_session(self):
        self.state = 'close'

    def start_session(self):
        self.state = 'running'
        self.running_date = fields.Datetime.now()
        self.agent_user_id = self.env.user
        try:
            sla = self.env['sla.whatsapp.session'].search([('tata_session_id','=',self.id)],limit=1)
            if sla:
                sla.state = "running"
        except Exception:
            pass

    def _search_is_close_visible(self, operator, value):
        if operator not in ['=', '!='] or not isinstance(value, bool):
            raise UserError(_('Operation not supported'))
        before_20 = datetime.now() - timedelta(hours=0, minutes=20)
        result_query = self.env['tata.whatsapp.session.2']._search([('last_massage_datetime', '<', before_20)])
        if (operator == '!=' and value is True) or (operator == '=' and value is False):
            domain_operator = 'not in'
        else:
            domain_operator = 'in'
        return [('id', domain_operator, result_query)]

    def create_opportunity_wizard(self):
        existing_opportunities = False
        partner = self.env['res.partner'].search([('phone', '=', self.customer_number)], limit=1)
        if partner:
            existing_opportunities = self.env['crm.lead'].search([('partner_id', '=', partner.id)])
        self.state = 'close'    
        return {
            'name': 'Convert to Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'tata.whatsapp.opportunity.convert.wizard',
            'view_mode': 'form',
            'context': {
                'default_whatsapp_session2_id': self.id,
                'default_conversion_action': 'merge' if existing_opportunities else 'convert',
                'default_user_id': self.env.user.id,
                'default_partner_action': 'exist' if partner else 'create',
                'default_partner_id': partner.id if partner else False,
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
            'domain': [('whatsapp_session2_id', '=', self.id)],
        }

    def get_image_url(self, image_id):
        url = 'https://wb.omni.tatatelebusiness.com/whatsapp-cloud/media/download/'+ image_id
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        if not access_token:
            raise ValidationError("Enter Session token first")
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
        }
        response = requests.get(url=url, headers=headers)
        data = json.loads(response.content.decode("utf-8"))
        return data

    def _prepare_send_image(self):
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/media"
        session_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        headers = {
            "accept": "application/json",
            "Authorization": session_token,
        }
        if not self.product_image:
            return {"error": "No image found"}
        image_data = base64.b64decode(self.product_image)
        mime_type = mimetypes.guess_type(self.file_name)[0] or "application/octet-stream"

        files = {
            "file": (self.file_name, image_data, mime_type)
        }

        # Send request
        response = requests.post(url, headers=headers, files=files)

        # Check response status
        if response.status_code in [200, 201]: 
            data = json.loads(response.content.decode("utf-8"))
            if mime_type.startswith("image/"):
                send_image = self.action_send_image(data["id"])
            else:
                send_image = self.action_send_document(data["id"])

            if send_image.status_code in [200, 201]:
                attachment_vals = {
                    'name': self.file_name,
                    'datas': self.product_image,
                    'type': 'binary',
                    'res_model': 'tata.whatsapp.session.2',
                    'res_id': self.id,
                }
                attachment = self.env['ir.attachment'].sudo().create(attachment_vals)
        return True

    def action_send_image(self, image_id):
        token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
        access_token = token
        if not access_token:
            raise ValidationError("Enter Session token first")
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
            "Content-Type": 'application/json',
        }
        data = {
            "to": "{{+%s}}" % self.customer_number,
            "type": "image",
            "source": "external",
            "image": {
                "id": image_id
            }
        }
        response = requests.post(url=url, headers=headers, json=data)
        return response

    def action_send_document(self, document_id):
        token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"

        headers = {
            "accept": 'application/json',
            "Authorization": token,
            "Content-Type": 'application/json',
        }

        data = {
            "to": "{{+%s}}" % self.customer_number,
            "type": "document",
            "source": "external",
            "document": {
                "id": document_id,
                "filename": self.file_name
            }
        }

        response = requests.post(url=url, headers=headers, json=data)
        return response

  

    def action_send_message(self):
        if self.send_message:
            url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
            access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
            if not access_token:
                raise ValidationError("Enter Session token first")
            headers = {
                "accept": 'application/json',
                "Authorization": access_token,
                "Content-Type": 'application/json',
            }
            data = {
                "to": "{{+%s}}" % self.customer_number,
                "type": "text",
                "source": "external",
                "text": {
                    "body": self.send_message
                }
            }
            response = requests.post(url=url, headers=headers, json=data)
            if response.status_code in [200, 201]:
                response_json = json.loads(response.text)
                self.message_post(body=self.send_message)
                self.write({'send_message': ''})
                if 'id' in response_json:
                    self.write({'sess_id': response_json['id']})
        if self.product_image:
            self._prepare_send_image()
        return True




class TataWhatsappMessages2(models.Model):
    _name = 'tata.whatsapp.messages.2'
    _description = 'Tata Whatsapp Messages 2'

    session_id = fields.Many2one('tata.whatsapp.session.2', string='Session')
    business_phone_number = fields.Char(string='Business Phone Number')
    business_id = fields.Char(string='Business ID')
    wa_id = fields.Char(string='WA ID')
    customer_name = fields.Char(string='Customer Name')
    customer_number = fields.Char(string='Customer Number')
    message_id = fields.Char(string='Message ID')
    message_date = fields.Datetime(string='Date')
    message_text = fields.Text(string='Message')
    message_type = fields.Selection([('text', 'Text'), ('image', 'Image')], string='Message Type')
    send_message = fields.Text(string='Send Message')

    def action_send_message(self):
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        if not access_token:
            raise ValidationError("Enter Session token first")
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
            "Content-Type": 'application/json',
        }
        data = {
            "to": "{{+%s}}" % self.session_id.customer_number,
            "type": "text",
            "source": "external",
            "text": {
                "body": self.send_message
            }
        }
        response = requests.post(url=url, headers=headers, json=data)


class HabooWhatupUserSession2(models.Model):
    _name = 'whatup.user.session.2'
    _description = 'Whatup User Session 2'

    name = fields.Char(string="Session Name")
    user_ids = fields.Many2many("res.users", 'whatup_user_session_2_res_users_rel', 'session_id', 'user_id', string="User")
