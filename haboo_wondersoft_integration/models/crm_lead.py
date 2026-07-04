from odoo import models, fields, api, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    wondersoft_order_no = fields.Char()

    def update_sale_order_wondersoft(self):
        call_closed_stage = self.env['crm.stage'].search([('is_won', '=', True)], limit=1)
        sale_order = self.env['sale.order'].search([('name', '=', self.wondersoft_order_no)])
        if sale_order:
            sale_order.update({'opportunity_id': self.id})
            self.write({'fulfillment_status': 'fulfilled'})
            if call_closed_stage:
                self.update({'stage_id': call_closed_stage.id})