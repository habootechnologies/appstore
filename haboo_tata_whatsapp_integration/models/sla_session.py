# -*- coding: utf-8 -*-

from odoo import models, fields


class SlaWhatsappSession(models.Model):
    _name = 'sla.whatsapp.session'
    _description = 'SLA WhatsApp Session'

    tata_session_id = fields.Many2one('tata.whatsapp.session', string='Session (Line 1)')
    tata_session2_id = fields.Many2one('tata.whatsapp.session.2', string='Session (Line 2)')
    state = fields.Selection(
        [('new', 'New'), ('running', 'Running'), ('close', 'Closed')],
        string='State', default='new'
    )
    name = fields.Char(string='Name')
