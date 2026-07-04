# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TataOpportunityConvertWizard(models.Model):
    _name = 'tata.opportunity.convert.wizard'
    _description = 'Tata Opportunity Wizard'

    whatsapp_session_id = fields.Many2one('tata.whatsapp.session', 'Whatsapp Session')
    conversion_action = fields.Selection(
        [('convert', 'Convert to Opportunity'), ('merge', 'Merge with existing Opportunities')],
        string='Coversion Action', default='convert')
    user_id = fields.Many2one('res.users', string='Salesperson')
    # team_id = fields.Many2one('crm.team', string='Sales Team', compute='compute_team_id')
    partner_action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
    ], string='Customer Action')
    partner_id = fields.Many2one('res.partner', string='Customer')
    existing_opportunities_ids = fields.One2many('existing.tata.opportunity.line', 'wizard_id',
                                                 string='Existing Opportunities')
    opportunity_ids = fields.Many2many('crm.lead', string='Existing Opportunities')

    # @api.depends('user_id')
    # def compute_team_id(self):
    #     for rec in self:
    #         team_member_id = self.env['crm.team.member'].search([('user_id', '=', rec.user_id.id)], limit=1)
    #         if team_member_id:
    #             rec.team_id = team_member_id.crm_team_id.id
    #         else:
    #             rec.team_id = False

    def action_create_opportunity(self):
        if self.conversion_action == 'convert':
            lead_source = self.env['lead.source.config'].search([('code', '=', 'WHATSAPP')], limit=1)
            partner_id = False
            if self.partner_action == "create":
                partner_id = self.env['res.partner'].create({
                    'name': "XXXXXX",
                    'phone': self.whatsapp_session_id.customer_number
                })

            opportunity = self.env['crm.lead'].sudo().create({
                'type': 'opportunity',
                'name': partner_id.name + "'s Opportunity" if partner_id else self.whatsapp_session_id.customer_name,
                'partner_id': self.partner_id.id if self.partner_action == 'exist' and self.partner_id else partner_id.id if partner_id else False,
                'whatsapp_session_id': self.whatsapp_session_id.id,
                'phone': partner_id.phone if partner_id else self.whatsapp_session_id.customer_number,
                'lead_source_id': lead_source.id if lead_source else False,
                'user_id': self.user_id.id if self.user_id else False,
                # 'team_id': self.team_id.id if self.team_id else False,
            })
            self.whatsapp_session_id.opportunity_id = opportunity.id
            print("--------", self.whatsapp_session_id.opportunity_id,"----self.whatsapp_session_id.opportunity_id---\n")
            return {
                'name': 'Opportunity',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': opportunity.id if opportunity else False,
                'target': 'current'
            }

    # def button_link(self):
    #     lead = self.env['crm.lead'].search([('partner_id', '=', self.partner_id.id)], limit=1)
    #     lead.write({'cdr_ids': [(6, 0, self.env.context.get('active_ids'))]})

    # def button_link(self):
    #     selected_opp = self.existing_opportunities_ids.filtered(lambda x: x.select_opportunity)
    #     # if not selected_opp:
    #     #     raise UserError('Select any one of the Existing Opportunities to link with')
    #     # if len(selected_opp):
    #     #     raise UserError('You can select only one of the Existing Opportunities to link with')
    #     # lead = self.env['crm.lead'].search([('cdr_id', 'in', self.cdr_id.id)], limit=1)
    #     # if lead:
    #     #     raise UserError(_('This Call Record is already linked to another Opportunity - %s') % lead.name)
    #     self.existing_opportunities_ids.filtered(lambda x: x.select_opportunity).write({'cdr_ids': [(6, 0, self.wizard_id.cdr_id.id)]})
    #     self.wizard_id.unlink()


class ExistingOpportunityLine(models.TransientModel):
    _name = 'existing.tata.opportunity.line'

    wizard_id = fields.Many2one('tata.opportunity.convert.wizard', string='Wizard')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')

    # def button_link(self):
    #     self.ensure_one()
    #     self.env.cr.commit()
    #     lead = self.env['crm.lead'].search([('whatsapp_session', 'in', self.wizard_id.cdr_id.id)], limit=1)
    #     if lead:
    #         raise UserError(_('This Call Record is already linked to another Opportunity - %s') % lead.name)
    #     self.opportunity_id.write({'cdr_ids': [(6, 0, self.wizard_id.cdr_id.id)]})
    #     return {'type': 'ir.actions.act_window_close'}


