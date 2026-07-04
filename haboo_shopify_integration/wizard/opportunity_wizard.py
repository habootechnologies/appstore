# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OpportunityConvertWizard(models.TransientModel):
    _name = 'shopify.opportunity.convert.wizard'
    _description = 'Convert to Opportunity'

    shopify_id = fields.Many2one('abandoned.checkouts', string='Shopify')
    conversion_action = fields.Selection([('convert', 'Convert to Opportunity'), ('merge', 'Merge with existing Opportunities')], string='Coversion Action', default='convert')
    user_id = fields.Many2one('res.users', string='Agent Name')
    team_id = fields.Many2one('crm.team', string='Sales Team', compute='compute_team_id')
    partner_action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ], string='Customer Action')
    partner_id = fields.Many2one('res.partner', string='Customer')
    partner_name = fields.Char(string='Customer Name')
    phone = fields.Char(string='Phone')
    email = fields.Char()
    client_number = fields.Char(string='Client Number')
    existing_opportunities_ids = fields.One2many('shopify.existing.opportunity.line', 'wizard_id', string='Existing Opportunities')
    opportunity_ids = fields.Many2many('crm.lead', string='Existing Opportunities')

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
            leads = self.env['crm.lead'].search([('phone', '=', rec.shopify_id.phone)])
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

    def action_create_opportunity(self):
        print("----------",self.shopify_id.is_boolean,"----'self.shopify_id.is_boolean'-------")
        if self.conversion_action == 'convert':
            lead_source = self.env['lead.source.config'].search([('code', '=', 'SHOPIFY')], limit=1)
            print("-----------", lead_source,"-----lead_source------\n")
            partner_id = False
            if self.partner_action == 'create':
                # if not self.partner_name:
                #     raise UserError("Kindly enter Customer Name")
                # if not self.phone:
                #     raise UserError("Kindly enter Customer Number")
                partner_id = self.env['res.partner'].create({
                    'name': self.partner_name,
                    'phone': self.phone,
                })
            opportunity = self.env['crm.lead'].sudo().create({
                'type': 'opportunity',
                'name': self.partner_id.name + "'s Opportunity" if self.partner_id else partner_id.name,
                'partner_id': self.partner_id.id if self.partner_action == 'exist' and self.partner_id else partner_id.id,
                'shopify_history_ids': [(6, 0, self.env.context.get('active_ids', []))],
                'phone': self.phone,
                'email_from':self.email,
                'lead_source_id': lead_source.id if lead_source else False,
                'user_id': self.user_id.id if self.user_id else False,
                'team_id': self.team_id.id if self.team_id else False,
                'from_conversion_shopify':True if self.partner_action == 'create' else False,
                'opportunity_line': [
                    (0, 0, {
                        'product_id': line.shopify_product_template_id.id,
                        'sku_code': line.sku_code,
                        'product_category': line.shopify_product_template_id.categ_id.id,
                        'product_qty': line.quantity,
                        'product_uom': line.product_uom_id.id,
                        'price_unit': line.price_unit,
                        'product_total_price': line.price_total,
                    }) for line in self.shopify_id.abandoned_checkouts_lines_ids
                ]

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
        lead.write({'shopify_history_ids': [(6, 0, self.env.context.get('active_ids'))]})

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
    _name = 'shopify.existing.opportunity.line'

    wizard_id = fields.Many2one('shopify.opportunity.convert.wizard', string='Wizard')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')

    def button_link(self):
        self.ensure_one()
        self.env.cr.commit()
        lead = self.env['crm.lead'].search([('shopify_id', 'in', self.wizard_id.shopify_id.id)], limit=1)
        if lead:
            raise UserError(_('This Shopify Abandoned is already linked to another Opportunity - %s') % lead.name)
        self.opportunity_id.write({'shopify_history_ids': [(6, 0, self.wizard_id.shopify_id.id)]})
        return {'type': 'ir.actions.act_window_close'}


