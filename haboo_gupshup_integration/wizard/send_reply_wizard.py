# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import urllib.parse



class SendReplyWizard(models.Model):
    _name = 'send.reply.wizard'
    _description = 'Send Reply Wizard'

    message_id = fields.Many2one('gupshup.whatsapp.messages', string='Message ID')
    sender_number = fields.Char(string='Sender Number')
    message = fields.Text(string='Message')

    def action_send_reply(self):
        url = self.env['ir.config_parameter'].sudo().get_param('haboo_gupshup_integration.gupshup_url', False)
        user_id = self.env['ir.config_parameter'].sudo().get_param('haboo_gupshup_integration.gupshup_userid', False)
        password = self.env['ir.config_parameter'].sudo().get_param('haboo_gupshup_integration.gupshup_password', False)
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }

        params = {
            "method": "SENDMESSAGE",
            "userid": user_id,
            "password": password,
            "auth_scheme": "plain",
            "v": "1.1",
            "send_to": self.sender_number,
            "format": "json",
            "msg": urllib.parse.quote(self.message),
            "msg_type": "HSM",
            "isHSM": 'true',
        }
        response = requests.post(url=url, json=params)
        print("--------", response,"----response---\n")
        print("--------", response.text,"----response---\n")