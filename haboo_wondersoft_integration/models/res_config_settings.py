from odoo import models, fields, api
import requests
import xmltodict


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wondersoft_access_token = fields.Char(config_parameter='haboo_wondersoft_integration.wondersoft_access_token')
    wondersoft_access_token_url = fields.Char(config_parameter='haboo_wondersoft_integration.wondersoft_access_token_url')


