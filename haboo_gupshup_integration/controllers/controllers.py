# -*- coding: utf-8 -*-
import base64
import json

import requests

from odoo import http
from odoo.http import request
import json
from datetime import datetime

class GupshupWhatsappWebhook(http.Controller):

    @http.route('/whatsapp/messages', type='http', auth='public', methods=['POST'], csrf=False)
    def gupshup_whatsapp_messages_webhook(self, **kw):
        data = json.loads(request.httprequest.data.decode("utf-8"))
        print("--------", data,"----data---\n")
        format_string = "%Y-%m-%d %H:%M:%S"
        timestamp_s = int(data['timestamp']) / 1000
        image_details = None
        if 'image' in data:
            image_details = json.loads(data['image'])
        request.env['gupshup.whatsapp.messages'].sudo().create({
            'sender_name': data['name'],
            'sender_number': data['mobile'],
            'wa_number': data['waNumber'],
            'message': data['text'] if data['type'] == 'text' else '',
            'image_url': image_details['url'] + image_details['signature'] if data['type'] == 'image' else '',
            'message_type': data['type'],
            'date': datetime.fromtimestamp(timestamp_s),
        })



class WhatsAppDLRController(http.Controller):
    @http.route('/whatsapp/dlr', type='json', auth='public', methods=['POST'], csrf=False)
    def handle_dlr(self, **post):
        print("--------DLR URL running------\n")
        print("--------", post,"----post---\n")
        # Example fields, adjust based on your DLR provider's response format
        message_id = post.get('message_id')
        delivery_status = post.get('status')

        # Find the corresponding message record in Odoo and update status
        if message_id:
            message = request.env['gupshup.whatsapp.messages'].sudo().search([('message_id', '=', message_id)], limit=1)
            if message:
                message.delivery_status = delivery_status
                # Update any additional fields if needed

        # Send a success response
        return {"status": "success"}
