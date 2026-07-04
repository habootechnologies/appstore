from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class PopWizard(models.TransientModel):
    _name = 'pop.wizard'
    _description = 'pop Wizard'

    customer_name = fields.Char()
    cdr_history_ids = fields.Many2many('cdr.history')

    opportunity_wizard_id = fields.Many2one('opportunity.convert.wizard')
    opportunity_pop_ids = fields.Many2many('crm.lead')

    def action_yes(self):
        self.ensure_one()
        wizard_id = self.env.context.get('active_id')
        wizard = self.env['opportunity.convert.wizard'].browse(wizard_id)
        wizard.partner_name = self.customer_name
        wizard.action_create_opportunity()
        return {'type': 'ir.actions.act_window_close'}
        # if not self.customer_name:
        #     raise ValidationError(_('Kindly enter the customer name.'))
        # if self.opportunity_wizard_id:
        #     self.opportunity_wizard_id.partner_name = self.customer_name
        #     self.opportunity_wizard_id.pop_boolean = True
        #     return {'type': 'ir.actions.act_window_close'}

    def action_no(self):
        self.ensure_one()
        if self.opportunity_wizard_id:
            self.opportunity_wizard_id.partner_name = self.customer_name or "XXXXXXXX"
            return {'type': 'ir.actions.act_window_close'}







