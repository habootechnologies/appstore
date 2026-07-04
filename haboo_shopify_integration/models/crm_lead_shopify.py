from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    shopify_order_no = fields.Char()
    shopify_history_ids = fields.Many2many('abandoned.checkouts', string='Shopify Abandoned Checkouts')
    from_conversion_shopify = fields.Boolean(string='From Shopify Conversion')
    fulfillment_status = fields.Selection(
        [('fulfilled', 'Fulfilled'), ('unfulfilled', 'Unfulfilled')],
        string='Fulfillment Status'
    )

    def view_shopify_abandoned_history(self):
        return {
            'name': 'shopify abandoned History',
            'type': 'ir.actions.act_window',
            'res_model': 'abandoned.checkouts',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.shopify_history_ids.ids)],
            'context': {
                'create': False,
                'delete': False,
            }
        }


    def update_sale_order(self):
        sale_order = self.env['sale.order'].search([('name', '=', self.shopify_order_no)])
        call_closed_stage = self.env['crm.stage'].search([('is_won', '=', True)], limit=1)
        if sale_order:
            sale_order.update({'opportunity_id': self.id})
            self.write({'fulfillment_status': 'fulfilled'})
        if call_closed_stage:
            self.update({'stage_id': call_closed_stage.id})




