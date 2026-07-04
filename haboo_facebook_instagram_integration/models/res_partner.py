from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    instagram_account_id = fields.Char("Instagram ID")
    messenger_account_id = fields.Char("Messenger ID")
