# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TataWhatsappOpportunityConvertWizard(models.Model):
    _name = 'tata.whatsapp.opportunity.convert.wizard'
    _description = 'Tata Whatsapp Opportunity Wizard'

    whatsapp_session2_id = fields.Many2one('tata.whatsapp.session.2', 'Whatsapp Session 2')
    conversion_action = fields.Selection(
        [('convert', 'Convert to Opportunity'), ('merge', 'Merge with existing Opportunities')],
        string='Coversion Action', default='convert')
    user_id = fields.Many2one('res.users', string='Salesperson')
    partner_action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
    ], string='Customer Action')
    partner_id = fields.Many2one('res.partner', string='Customer')
    existing_opportunities_ids = fields.One2many('existing.tata.whatsapp.opportunity.line', 'wizard_id',
                                                 string='Existing Opportunities')
    opportunity_ids = fields.Many2many('crm.lead', 'tata_wp2_wizard_crm_lead_rel', 'wizard_id', 'lead_id',
                                       string='Existing Opportunities')

    def action_create_opportunity(self):
        if self.conversion_action == 'convert':
            lead_source = self.env['lead.source.config'].search([('code', '=', 'WHATSAPP2')], limit=1)
            partner_id = False
            if self.partner_action == "create":
                partner_id = self.env['res.partner'].create({
                    'name': "XXXXXX",
                    'phone': self.whatsapp_session2_id.customer_number
                })

            vals = {
                'type': 'opportunity',
                'name': partner_id.name + "'s Opportunity" if partner_id else self.whatsapp_session2_id.customer_name,
                'partner_id': self.partner_id.id if self.partner_action == 'exist' and self.partner_id else partner_id.id if partner_id else False,
                'whatsapp_session2_id': self.whatsapp_session2_id.id,
                'phone': partner_id.phone if partner_id else self.whatsapp_session2_id.customer_number,
                'user_id': self.user_id.id if self.user_id else False,
            }
            if lead_source:
                vals['lead_source_id'] = lead_source.id
            opportunity = self.env['crm.lead'].sudo().create(vals)
            self.whatsapp_session2_id.opportunity_id = opportunity.id
            return {
                'name': 'Opportunity',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': opportunity.id,
                'target': 'current'
            }


class ExistingTataWhatsappOpportunityLine(models.TransientModel):
    _name = 'existing.tata.whatsapp.opportunity.line'
    _description = 'Existing Tata Whatsapp Opportunity Line'

    wizard_id = fields.Many2one('tata.whatsapp.opportunity.convert.wizard', string='Wizard')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')
