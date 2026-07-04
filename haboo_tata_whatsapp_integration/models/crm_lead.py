# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    whatsapp_session_id = fields.Many2one('tata.whatsapp.session', string='Whatsapp Session')
    whatsapp_session2_id = fields.Many2one('tata.whatsapp.session.2', string='Whatsapp Session 2', ondelete='set null')
    new_customer_opporunity = fields.Boolean(string='New Customer Opportunity')
    from_conversion_shopify = fields.Boolean(string='From Shopify Conversion')

    def view_whatsapp_session_2(self):
        session_id = self.env['tata.whatsapp.session.2'].search([('opportunity_id', '=', self.id)])
        return {
            'name': 'Whatsapp Session 2',
            'type': 'ir.actions.act_window',
            'res_model': 'tata.whatsapp.session.2',
            'view_mode': 'list,form',
            'domain': [('id', 'in', session_id.ids if session_id else [])],
            'context': {
                'create': False,
                'delete': False,
            }
        }

    def new_whatsapp_session_2(self):
        whatsapp_opportunity = self.env['tata.whatsapp.session.2'].search([('opportunity_id', '=', self.id), ('state', 'in', ['new', 'running'])])
        if whatsapp_opportunity:
            self.whatsapp_session2_id = whatsapp_opportunity[0]
            return {
                'name': 'Whatsapp Session 2',
                'type': 'ir.actions.act_window',
                'res_model': 'tata.whatsapp.session.2',
                'view_mode': 'list,form',
                'domain': [('opportunity_id', '=', self.id)],
                'context': {
                    'create': False,
                    'delete': False,
                }
            }
        else:
            if (self.partner_id and self.partner_id.phone) or self.phone:
                self.whatsapp_session2_id = self.env['tata.whatsapp.session.2'].sudo().create({
                    'opportunity_id': self.id,
                    'customer_name': self.partner_id.name,
                    'customer_number': self.partner_id.phone,
                    'session_id': self.name,
                })

                if self.new_customer_opporunity:
                    self.whatsapp_session2_id.new_send_whatsapp_message_2()

                elif self.from_conversion_shopify:
                    self.whatsapp_session2_id.new_send_whatsapp_message_shopify_2()

                return {
                    'name': 'Whatsapp Session 2',
                    'type': 'ir.actions.act_window',
                    'res_model': 'tata.whatsapp.session.2',
                    'view_mode': 'form',
                    'res_id': self.whatsapp_session2_id.id,
                    'context': {
                        'create': False,
                        'delete': False,
                    }
                }
        return True

    def view_whatsapp_session(self):
        session_id = self.env['tata.whatsapp.session'].search([]).filtered(lambda x: x.opportunity_id.id == self.id)
        print("--------", session_id,"----session_id---\n")
        return {
            'name': 'Whatsapp Session',
            'type': 'ir.actions.act_window',
            'res_model': 'tata.whatsapp.session',
            'view_mode': 'list,form',
            'domain': [('id', 'in',session_id.ids if session_id else [])],
            'context': {
                'create': False,
                'delete': False,
            }
        }

    # def new_whatsapp_session(self):
    #     if (self.partner_id and self.partner_id.phone) or self.phone:
    #         self.whatsapp_session_id = self.env['tata.whatsapp.session'].sudo().create({'opportunity_id': self.id, 'customer_name': self.partner_id.name, 'customer_number': self.partner_id.phone, 'session_id': self.name,'new_opporunity':self.new_customer_opporunity})
    #         return {
    #             'name': 'Whatsapp Session',
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'tata.whatsapp.session',
    #             'view_mode': 'form',
    #             'res_id': self.whatsapp_session_id.id,
    #             'context': {
    #                 'create': False,
    #                 'delete': False,
    #             }
    #         }
    #     return True

    def new_whatsapp_session(self):
        whatsapp_opportunity = self.env['tata.whatsapp.session'].search([('opportunity_id','=',self.id),('state', 'in', ['new', 'running'])])
        print("--------", whatsapp_opportunity,"----whatsapp_opportunity---\n")
        if whatsapp_opportunity:
            self.whatsapp_session_id = whatsapp_opportunity[0]
            return {
                'name': 'Whatsapp Session',
                'type': 'ir.actions.act_window',
                'res_model': 'tata.whatsapp.session',
                'view_mode': 'list,form',
                'domain': [('opportunity_id', '=', self.id)],
                'context': {
                    'create': False,
                    'delete': False,
                }
            }
        else:
            if (self.partner_id and self.partner_id.phone) or self.phone:
                self.whatsapp_session_id = self.env['tata.whatsapp.session'].sudo().create({
                    'opportunity_id': self.id,
                    'customer_name': self.partner_id.name,
                    'customer_number': self.partner_id.phone,
                    'session_id': self.name,
                })


                if self.new_customer_opporunity:
                    self.whatsapp_session_id.new_send_whatsapp_message()

                elif self.from_conversion_shopify:
                    self.whatsapp_session_id.new_send_whatsapp_message_shopify()

                return {
                    'name': 'Whatsapp Session',
                    'type': 'ir.actions.act_window',
                    'res_model': 'tata.whatsapp.session',
                    'view_mode': 'form',
                    'res_id': self.whatsapp_session_id.id,
                    'context': {
                        'create': False,
                        'delete': False,
                    }
                }
        return True


class HabooWhatupUserSession(models.Model):
    _name = 'whatup.user.session'

    name = fields.Char(string="Session Name")
    user_ids = fields.Many2many("res.users", string="User")