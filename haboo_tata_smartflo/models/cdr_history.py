# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import json
from datetime import date, datetime, time

class CallDetailRecords(models.Model):
    _name = 'cdr.history'
    _description = 'CDR History'
    _rec_name = 'call_id'

    log_id = fields.Char(string='Log ID')
    call_id = fields.Char(string='Call ID')
    call_direction = fields.Selection([('inbound', 'Incoming'), ('outbound', 'Outgoing')], string='Call Direction')
    call_description = fields.Char(string='Description')
    call_status = fields.Selection([('missed', 'Missed'), ('answered', 'Answered')], string='Call Status')
    call_recording_url = fields.Char(string='Call Recording')
    call_date = fields.Datetime(string='Date', default=datetime.today())
    call_region = fields.Char(string='Region')
    call_duration = fields.Char(string='Duration')
    department_name = fields.Char(string='Department Name')
    agent_user_id = fields.Many2one("res.users", "Agent User")
    agent_name = fields.Char(string='Agent Name')
    agent_number = fields.Char(string='Agent Number')
    client_number = fields.Char(string='Client Number', store=True)
    notes = fields.Text(string='Notes')
    send_reminder = fields.Boolean()
    client_id = fields.Many2one('res.partner', compute='_compute_client_name', store=True, )
    agent_name_id = fields.Many2one('res.partner', compute='_compute_agent_name', store=True, )
    is_converted = fields.Boolean(string="Converted to Opportunity", default=True)
    call_transcript = fields.Text(string="Call Transcript")
    transcription_text = fields.Text(string="Call Transcript")
    general_conversation = fields.Boolean("General Conversation")
    remark = fields.Text("Remark")
    sla_boo = fields.Boolean()


    def update_notes(self):
        # url = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_smartflo.note_update_url', False)
        url = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_smartflo.cdr_access_url', False)
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_smartflo.smartflo_access_token', False)
        today_date = datetime.combine(fields.Datetime.now(), time.min)
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + access_token,
            "from_date": str(today_date)
        }
        response = requests.get(url, headers=headers)
        active_url = 'https://api-smartflo.tatateleservices.com/v1/call/note/'
        active_url += str(self.log_id)
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_smartflo.smartflo_access_token', False)
        # url += str(self.call_id)
        payload = {
            "message": self.notes,
            "agent_disposition": 'None',
            "created_by": 'dheepa.s@futurenet.in',
        }
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + access_token,
            "content-type": "application/json",
        }
        response = requests.post(active_url, json=payload, headers=headers)
        print("--------", response.text,"----response---\n")

    def _update_cdr_history_data(self):
        url = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_smartflo.cdr_access_url', False)
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_tata_smartflo.smartflo_access_token', False)
        today_date = datetime.combine(fields.Datetime.now(), time.min)
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + access_token,
            "from_date": str(today_date)
        }
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        for record in data['results']:
            print("--------", record,"----record---\n")
            partner = self.env['res.partner'].search([('phone', '=', self.agent_number)], limit=1)
            print("-----------", partner,"-----partner.id------\n")
            existing_call_record = self.env['cdr.history'].search([('log_id', '=', record['id'])])
            if not existing_call_record:
                call_region = ''
                print("--------", record['circle'],"----record['circle']---\n")
                if record['circle'] and record['circle'] == 'International':
                    call_region += record['circle']
                elif record['circle'] and record['circle']['operator'] and record['circle']['circle']:
                    call_region += record['circle']['operator'] + '/' + record['circle']['circle']
                elif record['circle'] and record['circle']['operator']:
                    call_region += record['circle']['operator']
                elif record['circle'] and record['circle']['circle']:
                    call_region += record['circle']['circle']
                else:
                    call_region = ''
                values = {
                    'log_id': record['id'],
                    'call_id': record['call_id'],
                    'call_direction': record['direction'],
                    'call_description': record['description'] + '(' + record['service'] + ')',
                    'call_status': record['status'],
                    'call_recording_url': record['recording_url'],
                    'call_date': datetime.strptime(record['date'] + ' '  + record['time'], '%Y-%m-%d %H:%M:%S'),
                    'call_region': call_region,
                    'call_duration': str(record['call_duration']) + ' ' + 'Seconds',
                    'department_name': record['department_name'],
                    'agent_name': record['agent_name'],
                    'agent_number': record['agent_number'],
                    'client_number': record['client_number'],
                    'notes': record['notes']['message'] if record['notes'] else '',
                    'client_id':partner.id if partner else '',
                    'agent_name_id':partner.id if partner else '',

                }
                self.env['cdr.history'].create(values)

    def create_opportunity_wizard(self):
        self.sla_boo = True
        # partner = self.env['res.partner'].search([('phone', '=', self.client_number)], limit=1)
        partner = self.env['res.partner'].browse(self.client_id.id)
        # existing_opportunities = self.env['crm.lead'].search([('phone', '=', self.client_number)])
        domain = []
        if self.client_id:
            domain.append(('partner_id', '=', self.client_id.id))
        else:
            domain.append(('id', 'in', []))
        existing_opportunities = self.env['crm.lead'].search(domain)
        return {
            'name': 'Convert to Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'opportunity.convert.wizard',
            'view_mode': 'form',
            'context': {
                'default_cdr_ids': [(6, 0, self.id)],
                'default_conversion_action': 'merge' if existing_opportunities else 'convert',
                'default_user_id': self.env.user.id,
                'default_partner_action': 'exist' if partner else 'create',
                'default_partner_id': partner.id if partner else False,
                'default_client_number': self.client_number,
                'default_opportunity_ids': existing_opportunities.ids if existing_opportunities else False,
            },
            'target': 'new',
        }

    def auto_whatsapp_followup(self):
        today_date = date.today()
        print("--------", today_date,"----today_date---\n")
        print("--------", f"{today_date} 00:00:00","----111111111111111111111---\n")
        print("--------", f"{today_date} 23:59:59","----111111111111111111111---\n")
        send_reminders = self.search([('send_reminder', '=', True), ('call_status', '=', 'missed'), ('call_date', '>=', f"{today_date} 00:00:00"),('call_date', '<=', f"{today_date} 23:59:59")])
        print("--------", send_reminders,"----send_reminders---\n")
        for history in send_reminders:
            history.sudo().send_whatsapp_message()
            history.send_reminder = False
        return True

    def action_view_opportunity(self):
        return {
            'name': 'Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list,form',
            'domain': [('cdr_ids', 'in', self.id)],
        }

    @api.depends('agent_number')
    def _compute_agent_name(self):
        for rec in self:
            if rec.agent_number:
                agent_res = self.env['res.partner'].search([('phone','!=',False),('phone', 'in', [rec.agent_number])], limit=1)
                rec.agent_name_id = agent_res.id if agent_res else False
            else:
                rec.agent_name_id = False

    @api.depends('client_number')
    def _compute_client_name(self):
        for rec in self:
            if rec.client_number:
                client_res = self.env['res.partner'].search([('phone', '!=', False), ('phone', 'in', [rec.client_number])],limit=1)
                rec.client_id = client_res.id
            else:
                rec.client_id = False

    def send_whatsapp_message(self):
        url = "https://wb.omni.tatatelebusiness.com/whatsapp-cloud/messages"
        access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaG9uZU51bWJlciI6Iis5MTYzNjk0OTk1ODMiLCJwaG9uZU51bWJlcklkIjoiNTUxNzU4NTY4MDEzNDM2IiwiaWF0IjoxNzM1NTQ0ODcxfQ.xI47ViijN4ZdDeOs-h30wfaaQYxD_aSxwyf5e7dvFu8'
        headers = {
            "accept": 'application/json',
            "Authorization": access_token,
            "Content-Type": 'application/json',
        }
        # data = {
        #     "to": "{{+%s}}" % self.customer_number,
        #     "type": "text",
        #     "source": "external",
        #     "text": {
        #         "body": self.send_message
        #     }
        # }


        data = {
          "to": self.client_number,
          "type": "template",
          "source": "external",
          "template": {
            "name": "ivr_unansweredcalls",
            "language": {
              "code": "en"
            },
            "components": []
          }
        }
        response = requests.post(url=url, headers=headers, json=data)
        response_json = json.loads(response.text)
        print(response_json)
        # self.message_post(body=self.send_message)
        return True

class ResUsers(models.Model):
    _inherit = "res.users"

    phone = fields.Char(related='partner_id.phone')





