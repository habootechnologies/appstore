# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    cdr_ids = fields.Many2many('cdr.history', string='CDR')
    new_customer_opporunity = fields.Boolean(string='New Customer Opportunity')

    def view_call_history(self):
        return {
            'name': 'Call History',
            'type': 'ir.actions.act_window',
            'res_model': 'cdr.history',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.cdr_ids.ids)],
            'context': {
                'create': False,
                'delete': False,
            }
        }