from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    qikberry_session_id = fields.Many2one('qikchat.message', string='Qikberry Session')


    def view_whatsapp_session(self):
        session_id = self.env['qikchat.message'].search([]).filtered(lambda x: x.opportunity_id.id == self.id)
        print("--------", session_id,"----session_id---\n")
        return {
            'name': 'qikchat message',
            'type': 'ir.actions.act_window',
            'res_model': 'qikchat.message',
            'view_mode': 'list,form',
            'domain': [('id', 'in',session_id.ids if session_id else [])],
            'context': {
                'create': False,
                'delete': False,
            }
        }


