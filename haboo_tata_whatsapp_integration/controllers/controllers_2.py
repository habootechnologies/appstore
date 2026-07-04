from odoo import http, _
from odoo.http import request, Response
import json
from datetime import datetime ,date, timedelta
import os
import signal
import base64
import hashlib
from odoo.addons.bus.models.bus import dispatch
from hashlib import sha256
from base64 import b64encode
import requests
import logging
_logger = logging.getLogger(__name__)
import mimetypes
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError


class TataWhatsappWebhook2(http.Controller):

    @http.route('/dropzone/upload_2', type='json', auth='user', methods=['POST'], csrf=False)
    def upload_file(self, **kwargs):
        data = json.loads(request.httprequest.data.decode("utf-8"))
        filename = data["params"].get("filename")
        mimetype = data["params"].get("mimetype")
        file_data = data["params"].get("datas")
        thread = data["params"].get("thread")
        file = data["params"].get("file")
        if filename and mimetype and file_data and thread:
            response = self.send_dropimage_whatsup(filename, file_data, mimetype, thread)
        return response.status_code

    def send_dropimage_whatsup(self, filename, file_data, mimetype, thread):
        session_token = request.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/media"
        headers = {
            "accept": "application/json",
            "Authorization": session_token,
        }
        file_datas = base64.b64decode(file_data)
        if mimetype and mimetype.startswith("image/"):
            files = {
                "file": (filename, file_datas, mimetype)
            }
        else:
            files = { "files": ("","", "") }
        responses = requests.post(url, headers=headers, files=files)
        data = responses.json();
        if "id" in data:
            send_image = self.controller_action_send_image(data["id"], thread)
        else:
            send_image = responses
        return send_image

    @http.route('/send/wp/message_2', type='json', auth='user', methods=['POST'], csrf=False)
    def send_whatsapp_message(self, **kwargs):
        data = kwargs
        message_body = data.get("body", "")
        attachment_ids = data.get("attachment_ids", [])
        partner_ids = data.get("partner_ids", [])
        model = data.get("model", "")
        res_id = data.get("res_id", 0)
        if message_body:
            response = self.controller_send_message(message_body,res_id)
        if attachment_ids:
            response = self.send_attachment_whatup(attachment_ids, res_id)
        return response.status_code

    def controller_send_message(self,message_body, res_id):
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
        access_token = request.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        current_id = request.env['tata.whatsapp.session.2'].sudo().search([('id','=',res_id)],limit=1)
        if not access_token:
            raise ValidationError("Enter Session token first")

        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
            "Content-Type": 'application/json',
        }
        data = {
            "to": "{{+%s}}" % current_id.customer_number,
            "type": "text",
            "source": "external",
            "text": {
                "body": message_body
            }
        }
        response = requests.post(url=url, headers=headers, json=data)
        return response

    def send_attachment_whatup(self, attachment_ids, res_id):
        attachments = request.env["ir.attachment"].sudo().browse(attachment_ids)

        session_token = request.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/media"
        headers = {
            "accept": "application/json",
            "Authorization": session_token,
        }

        for attachment in attachments:
            image_data = base64.b64decode(attachment.datas)
            mime_type = mimetypes.guess_type(attachment.name)[0]
            if mime_type and mime_type.startswith("image/"):
                files = {
                    "file": (attachment.name, image_data, mime_type)
                }
            else:
                files ={
                    "files": ("","", "")
                }

            # Send request
            response = requests.post(url, headers=headers, files=files)
            data = response.json()
            if "id" in data:
                send_image = self.controller_action_send_image(data["id"], res_id)
            else:
                send_image = response  
        return send_image

    def controller_action_send_image(self, image_id, res_id):
        token = request.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
        current_id = request.env['tata.whatsapp.session.2'].sudo().search([('id','=',res_id)],limit=1)
        access_token = token
        if not access_token:
            raise ValidationError("Enter Session token first")
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
            "Content-Type": 'application/json',
        }
        data = {
            "to": "{{+%s}}" % current_id.customer_number,
            "type": "image",
            "source": "external",
            "image": {
                "id": image_id
            }
        }
        response = requests.post(url=url, headers=headers, json=data)
        return response

    def find_correct_user_id(self):
        next_user_id = False

        user_session = request.env['whatup.user.session.2'].sudo().search([], order='id ASC')
        all_user_ids = user_session.mapped('user_ids.id')
        if not all_user_ids:
            return False
        latest_session = request.env['tata.whatsapp.session.2'].sudo().search(
            [('state', '=', 'new'), ('agent_user_id', 'in', all_user_ids)], 
            order='create_date DESC',  
            limit=1
        )
        if not latest_session or not latest_session.agent_user_id:
            return False

        last_user_id = latest_session.agent_user_id.id  

        if last_user_id in all_user_ids:
            last_index = all_user_ids.index(last_user_id)  
            next_index = (last_index + 1) % len(all_user_ids) 
            next_user_id = all_user_ids[next_index]
        else:
            next_user_id = all_user_ids[0]

        return next_user_id

    @http.route('/tata/whatsapp/test2', type='http', auth='public', methods=['POST'], csrf=False)
    def tata_whatsapp_messages_test_webhook(self, **kw):
        user_id = self.find_correct_user_id()
        user = request.env['res.users']
        if user_id:
            user = request.env['res.users'].sudo().browse(user_id)
        channel = "whatsapp_channel_2"

        data = json.loads(request.httprequest.data.decode("utf-8"))
        ref_message = {
            "data": data,
            "channel": channel
        }
        message = "<b>Test</b>"
        request.env["bus.bus"]._sendone(
            user.partner_id,
            'simple_notification', {
                'title': _("Need Quotation Approval"),
                'message_is_html': message,
                "message": message,
                'sticky': False,
                'warning': True,
            })
        
        existing_session = request.env['tata.whatsapp.session.2'].sudo().search([], limit=1)
        
        message_rec = request.env['mail.message'].sudo().create({
            "message_type": 'comment', 
            'model': 'tata.whatsapp.session.2', 
            'res_id': existing_session.id, 
            "body": data.get('name', '')
        })

        request.env["bus.bus"]._sendone(channel, "notification", ref_message)

    #function for the sending notification chatter 
    def create_mail_notification(self, message_rec, notify_partner_id):
        notif_create_values = [{
            'author_id': message_rec.author_id.id,
            'mail_message_id': message_rec.id,
            'res_partner_id': notify_partner_id.id,
            'notification_type': 'sms',
            'notification_status': 'sent',
        }]
        request.env['mail.notification'].sudo().create(notif_create_values)
        return True

    def get_image_url(self, image_id):
        url = 'https://wb.omni.tatatelebusiness.com/whatsapp-cloud/media/download/'+ image_id
        access_token = request.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
        }
        response = requests.get(url=url, headers=headers)
        data = json.loads(response.content.decode("utf-8"))
        return data

    def get_video_url(self, video_id):
        url = 'https://wb.omni.tatatelebusiness.com/whatsapp-cloud/media/download/' + video_id
        access_token = request.env['ir.config_parameter'].sudo().get_param('haboo_tata_whatsapp_integration.session_token_2')

        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
        }
        response = requests.get(url, headers=headers)
        data = json.loads(response.content.decode("utf-8"))
        return data



    @http.route('/tata/whatsapp/messages2/json', type='json', auth='public', methods=['POST'], csrf=False)
    def tata_whatsapp_messages_webhook_json(self, **kw):
        data = json.loads(request.httprequest.data.decode("utf-8"))


    @http.route('/tata/whatsapp/messages2', type='http', auth='public', methods=['POST'], csrf=False)
    def tata_whatsapp_messages_webhook(self, **kw):
        data = json.loads(request.httprequest.data.decode("utf-8"))
        channel = "whatsapp_channel_2"
        partner = request.env['res.partner'].sudo().search([('phone', '=', data['contacts'][0]['wa_id'])], limit=1)
        user_id = self.find_correct_user_id()
        today = date.today();
        existing_session = request.env['tata.whatsapp.session.2'].sudo().search([('customer_number', '=', data['contacts'][0]['wa_id']), ('last_massage_datetime', '>', fields.Datetime.now() - timedelta(days=30))], limit=1)
        message = {
            "data": data,
            "channel": channel
        }
        if existing_session:
            if existing_session.state == 'close':
                existing_session.reopen_session()
        message_text = ''
        if data['messages']['type'] == 'text':
            message_text = data['messages']['text']['body']
        elif data['messages']['type'] == 'button':
            message_text = data['messages']['button']['text']
        attachments = request.env['ir.attachment']
        attachment_data = False
        notify_partner_id = request.env['res.partner']
        if data['messages']['type'] == 'image':
            image_id = data['messages']['image']['id']
            attachment_data = self.get_image_url(image_id=image_id)
        elif data['messages']['type'] == 'video':
            video_id = data['messages']['video']['id']
            attachment_data = self.get_video_url(video_id=video_id)

        if existing_session:
            notify_partner_id = existing_session.agent_user_id and existing_session.agent_user_id.partner_id
            if not partner:
                partner = request.env['res.partner'].sudo().create({'name': data['contacts'][0]['profile']['name'], 'phone': data['contacts'][0]['wa_id']})
            if attachment_data:
                response = requests.get(attachment_data['url'])
                attachments = attachments.sudo().create({
                        'name': attachment_data['url'],
                        'datas': base64.b64encode(response.content),
                        'res_id': existing_session.id,
                        'res_model': 'tata.whatsapp.session.2',
                        'type': 'binary',
                        'mimetype': attachment_data['mime_type']})
                message_rec = request.env['mail.message'].sudo().create({"attachment_ids": attachments.ids, "author_id": partner.id, "message_type": 'comment', 'model': 'tata.whatsapp.session.2', 'res_id': existing_session.id, "body": '-'})

            else:
                message_rec = request.env['mail.message'].sudo().create({"author_id": partner.id, "message_type": 'comment', 'model': 'tata.whatsapp.session.2', 'res_id': existing_session.id, "body": message_text})
        else:
            partner = request.env['res.partner'].sudo().create({
                'name': data['contacts'][0]['profile']['name'],
                'phone': data['contacts'][0]['wa_id'],
            })
            new_session = request.env['tata.whatsapp.session.2'].sudo().create({
                'session_id': data['id'],
                'customer_name': data['contacts'][0]['profile']['name'],
                'customer_number': data['contacts'][0]['wa_id'],
                'agent_user_id': user_id,
                'date': datetime.fromtimestamp(int(data['messages']['timestamp'])),

            })
            notify_partner_id = new_session.agent_user_id and new_session.agent_user_id.partner_id
            if attachment_data:
                response = requests.get(attachment_data['url'])
                attachments = attachments.sudo().create({
                        'name': attachment_data['url'],
                        'datas': base64.b64encode(response.content),
                        'res_id': new_session.id,
                        'res_model': 'tata.whatsapp.session.2',
                        'type': 'binary',
                        'mimetype': attachment_data['mime_type']})
                message_rec = request.env['mail.message'].sudo().create({"attachment_ids": attachments.ids, "author_id": partner.id, "message_type": 'comment', 'model': 'tata.whatsapp.session.2', 'res_id': new_session.id, "body": '-'})
            else:
                message_rec = request.env['mail.message'].sudo().create({"author_id": partner.id, "message_type": 'comment', 'model': 'tata.whatsapp.session.2', 'res_id': new_session.id, "body": message_text})
        if notify_partner_id:
            self.create_mail_notification(message_rec, notify_partner_id)
        whatsapp_message = "<b> New message received.. </b>"
        if notify_partner_id:
            request.env["bus.bus"]._sendone(
                notify_partner_id,
                'simple_notification', {
                    'title': _("Whatsapp Message (No.2)"),
                    'message_is_html': whatsapp_message,
                    'message': whatsapp_message,
                    'sticky': False,
                    'warning': False,
                })
        request.env["bus.bus"]._sendone(channel, "notification", message)

class TataWhatsappWebhookDLR2(http.Controller):

    @http.route('/tata/whatsapp/messages2/dlr', type='http', auth='public', methods=['POST'], csrf=False)
    def tata_whatsapp_messages_dlr_webhook(self, **kw):
        data = json.loads(request.httprequest.data.decode("utf-8"))
