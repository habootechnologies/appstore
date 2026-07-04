# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OpportunityConvertWizard(models.TransientModel):
    _name = 'opportunity.convert.wizard'
    _description = 'Convert to Opportunity'

    cdr_id = fields.Many2one('cdr.history', string='CDR')
    conversion_action = fields.Selection([('convert', 'Convert to Opportunity'), ('merge', 'Merge with existing Opportunities')], string='Coversion Action', default='convert')
    user_id = fields.Many2one('res.users',string='Agent Name')
    team_id = fields.Many2one('crm.team', string='Sales Team', compute='compute_team_id')
    partner_action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ], string='Customer Action')
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_name = fields.Char(string='Customer Name')
    client_number = fields.Char(string='Client Number')
    existing_opportunities_ids = fields.One2many('existing.opportunity.line', 'wizard_id', string='Existing Opportunities')
    opportunity_ids = fields.Many2many('crm.lead', string='Existing Opportunities')
    pop_wizard_id = fields.Many2one('pop.wizard')
    new_customer = fields.Boolean()
    pop_boolean = fields.Boolean()
    html = fields.Html(string='html', default='Do You Want to Change the Agent')
    yes_or_no = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'NO')], string='Agent')
    partner_action_transfer = fields.Selection([
        ('convert', 'Convert to Opportunity'),
    ], string='Coversion Action',default='convert')
    # @api.depends('partner_action')
    # def compute_convert_opportunity(self):
    #     for rec in self:
    #         if rec.partner_action == 'create':
    #             rec.new_customer = True
    #         else:
    #             rec.new_customer = False



    # @api.model
    # def default_get(self, fields):
    #     res = super(OpportunityConvertWizard, self).default_get(fields)
    #     print("--------", res,"----res---\n")
    #     team_member_id = self.env['crm.team.member'].search([('user_id', '=', res['user_id'])], limit=1)
    #     if team_member_id:
    #         res.update({'team_id': team_member_id.crm_team_id.id})
    #     leads = self.env['crm.lead'].search([('partner_id', '=', res['partner_id'])])
    #     print("--------", leads,"----leads---\n")
    #     if leads:
    #         for lead in leads:
    #             res.update({'existing_opportunities_ids': [(0, 0, {'opportunity_id': lead.id})]})
    #     return res

    @api.depends('partner_id')
    def compute_existing_opportunities(self):
        for rec in self:
            leads = self.env['crm.lead'].search([('phone', '=', rec.cdr_id.client_number)])
            if leads:
                for lead in leads:
                    rec.existing_opportunities_ids = [(0, 0, {'opportunity_id': lead.id})]
            else:
                rec.existing_opportunities_ids = False

    @api.depends('user_id')
    def compute_team_id(self):
        for rec in self:
            team_member_id = self.env['crm.team.member'].search([('user_id', '=', rec.user_id.id)], limit=1)
            if team_member_id:
                rec.team_id = team_member_id.crm_team_id.id
            else:
                rec.team_id = False

    # def action_pop_wizard(self):
    #     return {
    #         'name': _('Create Customer?'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'pop.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #     }

    def action_create_opportunity(self):
        if self.conversion_action == 'convert':
            lead_source = self.env['lead.source.config'].search([('code', '=', 'TATA')], limit=1)
            partner_id = False
            if self.partner_action == 'create':
                # if not self.partner_name:
                #     raise UserError("Kindly enter Customer Name")
                if not self.client_number:
                    raise UserError("Kindly enter Customer Number")
                partner_id = self.env['res.partner'].create({
                    'name': self.partner_name or "XXXXXXX",
                    'phone': self.client_number,
                })
            opportunity = self.env['crm.lead'].sudo().create({
                'type': 'opportunity',
                'name': self.partner_id.name + "'s Opportunity" if self.partner_id else partner_id.name,
                'partner_id': self.partner_id.id if self.partner_action == 'exist' and self.partner_id else partner_id.id,
                'cdr_ids': [(6, 0, self.env.context.get('active_ids'))],
                'phone': self.client_number,
                'lead_source_id': lead_source.id if lead_source else False,
                'user_id': self.user_id.id if self.user_id else False,
                'team_id': self.team_id.id if self.team_id else False,
                'new_customer_opporunity':True if self.partner_action == 'create' else False,
            })
            return {
                'name': 'Opportunity',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': opportunity.id,
                'target': 'current'
            }

    def button_link(self):
        lead = self.env['crm.lead'].search([('partner_id', '=', self.partner_id.id)], limit=1)
        lead.write({'cdr_ids': [(6, 0, self.env.context.get('active_ids'))]})

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

    def button_link(self):
        self.ensure_one()
        self.env.cr.commit()
        lead = self.env['crm.lead'].search([('cdr_id', 'in', self.wizard_id.cdr_id.id)], limit=1)
        if lead:
            raise UserError(_('This Call Record is already linked to another Opportunity - %s') % lead.name)
        self.opportunity_id.write({'cdr_ids': [(6, 0, self.wizard_id.cdr_id.id)]})
        return {'type': 'ir.actions.act_window_close'}


class OpportunityRequired(models.TransientModel):
    _name = 'opportunity.required'

    cdr_history_id = fields.Many2one('cdr.history', string='CDR History')
    html = fields.Html(string='html', default='Do You Want to Change the Agent')
    yes_or_no = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'NO')], string='Agent Transfert', default='yes')

    def yes_action(self):
        pass

    def no_action(self):
        pass
