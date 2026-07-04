# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cdr_access_url = fields.Char(string='CDR Access URL', config_parameter='haboo_tata_smartflo.cdr_access_url')
    note_update_url = fields.Char(string='Note Update URL', config_parameter='haboo_tata_smartflo.note_update_url')
    smartflo_access_token = fields.Char(string='Tata SmartFlo Access Token', config_parameter='haboo_tata_smartflo.smartflo_access_token')


