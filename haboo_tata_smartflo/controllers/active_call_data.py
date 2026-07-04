import base64
import json

import requests

from odoo import http
from odoo.http import request
import json
from datetime import datetime, timedelta

class ActiveCallWebhook(http.Controller):

    @http.route('/webhook/tata_smartcall/active_call', type='json', auth='public', methods=['POST'], csrf=False)
    def active_call_webhook(self, **kw):
        data = json.loads(request.httprequest.data.decode("utf-8"))
        customer_number = data['caller_id_number']
        if customer_number.isdigit() and len(customer_number) == 10:
            customer_number = "91" + customer_number
        # elif customer_number.startswith("91") and len(customer_number) == 12:
        #     customer_number = "+" + customer_number
        # elif not customer_number.startswith("+91"):
        #     customer_number = "+91" + customer_number.lstrip("+")
        call_date = datetime.strptime(data['start_stamp'], '%Y-%m-%d %H:%M:%S') - timedelta(hours=5, minutes=30)
        call_history = request.env['cdr.history'].sudo().create({
            'call_id': data['call_id'],
            'client_number': customer_number,
            'call_status': 'missed',
            'call_date': call_date,
            'send_reminder': True
        })
        # call_history.sudo().send_whatsapp_message()


    @http.route('/webhook/tata_smartcall/call_hangup', type='json', auth='public', methods=['POST'], csrf=False)
    def call_hangup_answered(self, **kw):
        data = json.loads(request.httprequest.data.decode("utf-8"))
        call_history = request.env["cdr.history"].sudo().search([("call_id", "=", data['call_id'])])
        call_date = datetime.strptime(data['start_stamp'], '%Y-%m-%d %H:%M:%S') - timedelta(hours=5, minutes=30)
        call_history.sudo().update({
            'call_id': data['call_id'],
            'call_duration': data['duration']  + ' ' + 'Seconds',
            'call_recording_url': data['recording_url'],
            'call_direction': data['direction'],
            'agent_number': data['answered_agent']['agent_number'],
            'call_date': call_date,
            'agent_name': data['answered_agent']['name'],
            'send_reminder': False,
            'call_status': 'answered',
        })

