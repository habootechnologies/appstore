from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_close_minute = fields.Integer(string='Auto session close after', config_parameter='haboo_tata_whatsapp_integration.auto_close_minute', default=20)    
    session_token = fields.Char(string='Access Token', config_parameter='haboo_tata_whatsapp_integration.session_token')
    auto_close_minute_2 = fields.Integer(string='Auto session close after (No.2)', config_parameter='haboo_tata_whatsapp_integration.auto_close_minute_2', default=20)
    session_token_2 = fields.Char(string='Access Token (No.2)', config_parameter='haboo_tata_whatsapp_integration.session_token_2')