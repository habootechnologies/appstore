# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gupshup_url = fields.Char(string='Gupshup URL', config_parameter='haboo_gupshup_integration.gupshup_url')
    gupshup_userid = fields.Char(string='Gupshup User ID', config_parameter='haboo_gupshup_integration.gupshup_userid')
    gupshup_password = fields.Char(string='Gupshup Password', config_parameter='haboo_gupshup_integration.gupshup_password')