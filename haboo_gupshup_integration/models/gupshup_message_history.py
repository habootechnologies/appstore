# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests


class GupshupMessageHistory(models.Model):
    _name = 'gupshup.whatsapp.messages'
    _description = 'Gupshup Whatsapp Messages'

    sender_name = fields.Char(string='Sender Name')
    sender_number = fields.Char(string='Sender Number')
    wa_number = fields.Char(string='Whatsapp Number')
    message = fields.Text(string='Message')
    image_url = fields.Char(string='Image URL')
    message_type = fields.Selection([('text', 'Text'), ('image', 'Image')])
    message_id = fields.Char(string='Message ID')
    date = fields.Datetime(string='Date')
    partner_id = fields.Many2one('res.partner', 'Customer')

    def create_send_reply(self):
        return {
            'name': 'Send Reply',
            'type': 'ir.actions.act_window',
            'res_model': 'send.reply.wizard',
            'view_mode': 'form',
            'context': {
                'default_message_id': self.id,
                'default_sender_number': self.sender_number,
            },
            'target': 'new',
        }

    def action_opt_in(self):
        url = self.env['ir.config_parameter'].sudo().get_param('haboo_gupshup_integration.gupshup_url', False)
        user_id = self.env['ir.config_parameter'].sudo().get_param('haboo_gupshup_integration.gupshup_userid', False)
        password = self.env['ir.config_parameter'].sudo().get_param('haboo_gupshup_integration.gupshup_password', False)
        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        params = {
            'method': "OPT_IN",
            'userid': user_id,
            'password': password,
            'auth_scheme': 'plain',
            'v': '1.1',
            'phone_number': self.sender_number,
            'channel': 'WHATSAPP',
        }
        response = requests.post(url=url, headers=headers, params=params)
        print("--------", response, "----response---\n")
        print("--------", response.text, "----response---\n")


    @api.model
    def create(self, vals):
        res = super(GupshupMessageHistory, self).create(vals)
        if vals['sender_number']:
            customer = self.env['res.partner'].search(['|', ('mobile', '=', vals['sender_number']), ('phone', '=', vals['sender_number'])], limit=1)
            if customer:
                res['partner_id'] = customer.id
        return res