# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OpportunityConvertWizard(models.Model):
    _name = 'opportunity.convert.session.wizard'
    _description = 'Opportunity Wizard'

    session_id = fields.Many2one('messenger.session', 'Session')
    comment_id = fields.Many2one('post.comments', 'Comments')
    customer_number = fields.Char(string='Customer Number')
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
    existing_opportunities_ids = fields.One2many('existing.opportunity.line', 'wizard_id',
                                                 string='Existing Opportunities')
    opportunity_ids = fields.Many2many('crm.lead', string='Existing Opportunities')
    provider_id = fields.Many2one("messenger.session", "Provider", readonly=True)

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
            provider = self.session_id.provider_id.name or ''
            session_id = self.session_id
            comment_id = self.comment_id
            customer_name = ''
            customer_number = ''
            if session_id:
            	customer_name = session_id.partner_id.name
            	customer_number = session_id.customer_number
            if comment_id:
            	customer_name = comment_id.username
            	customer_number = self.customer_number
            	
            opportunity = False
            if self.partner_id:
                opportunity = self.env['crm.lead'].sudo().create({
                    'type': 'opportunity',
                    'name': self.partner_id.name + "'s Opportunity" if self.partner_id else customer_name,
                    'partner_id': self.partner_id.id if self.partner_action and self.partner_id else False,
                    'session_id': session_id.id,
                    'comment_id': comment_id.id,
                    'phone': self.partner_id.phone if self.partner_id and self.partner_id.phone else 'xxxxxxxxxxxxxxxxx',
                    'lead_source_id': self.env['lead.source.config'].search(
                        [('code', '=',
                          'INSTAGRAM' if provider == 'Giri_Instagram' else 'FACEBOOK' if provider == 'Giri Facebook' else False)],
                        limit=1
                    ).id,
                    'user_id': self.user_id.id if self.user_id else False,
                    # 'team_id': self.team_id.id if self.team_id else False,
                })
            else:
                partner_id = self.env['res.partner'].create({'name': customer_name, 'phone': customer_number})
                opportunity = self.env['crm.lead'].sudo().create({
                    'type': 'opportunity',
                    'name': partner_id.name + "'s Opportunity" if partner_id else customer_name,
                    'partner_id': partner_id.id if partner_id else False,
                    'session_id': session_id.id,
                    'comment_id': comment_id.id,
                    'phone': self.partner_id.phone if self.partner_id and self.partner_id.phone else 'xxxxxxxxxxxxxxxxx',
                    'lead_source_id': self.env['lead.source.config'].search(
                        [('code', '=',
                          'INSTAGRAM' if provider == 'Giri_Instagram' else 'FACEBOOK' if provider == 'Giri Facebook' else False)],
                        limit=1
                    ).id,
                    'user_id': self.user_id.id if self.user_id else False,
                    # 'team_id': self.team_id.id if self.team_id else False,
                })
                if self.comment_id:
                    self.comment_id.partner_id = partner_id
                    self.comment_id.opportunity_id = opportunity.id
                if self.session_id:
                    self.session_id.partner_id = partner_id
                    self.session_id.opportunity_id = opportunity.id
            self.session_id.opportunity_id = opportunity.id

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
    _name = 'existing.opportunity.line'

    wizard_id = fields.Many2one('opportunity.convert.wizard', string='Wizard')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')

    # def button_link(self):
    #     self.ensure_one()
    #     self.env.cr.commit()
    #     lead = self.env['crm.lead'].search([('whatsapp_session', 'in', self.wizard_id.cdr_id.id)], limit=1)
    #     if lead:
    #         raise UserError(_('This Call Record is already linked to another Opportunity - %s') % lead.name)
    #     self.opportunity_id.write({'cdr_ids': [(6, 0, self.wizard_id.cdr_id.id)]})
    #     return {'type': 'ir.actions.act_window_close'}


