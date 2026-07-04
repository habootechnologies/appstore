from odoo import models, fields, api

class QikberryOpportunityConvertWizard(models.Model):
    _name = 'haboo_qikberry.opportunity.convert.wizard'
    _description = 'Qikberry Opportunity Wizard'

    qikberry_session_id = fields.Many2one('qikchat.message', 'Qikberry Session')
    conversion_action = fields.Selection(
        [('convert', 'Convert to Opportunity'), ('merge', 'Merge with existing Opportunities')],
        string='Coversion Action', default='convert')
    user_id = fields.Many2one('res.users', string='Salesperson')
    partner_action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
    ], string='Customer Action')
    partner_id = fields.Many2one('res.partner', string='Customer')
    existing_opportunities_ids = fields.One2many('existing.haboo_qikberry.opportunity.line', 'wizard_id',
                                                 string='Existing Opportunities')
    opportunity_ids = fields.Many2many('crm.lead', string='Existing Opportunities')

    def action_convert_opporunity(self):
        if self.conversion_action == 'convert':
            lead_source = self.env['lead.source.config'].search([('code', '=', 'QB')], limit=1)
            partner_id = False
            if self.partner_action == "create":
                partner = self.env['res.partner'].search([('phone','=',self.self.qikberry_session_id.to_contact)],limit=1)
                print("-----------", partner,"-----partner------\n")
                if not partner:
                    partner_id = self.env['res.partner'].create({
                        'name': "XXXXXX",
                        'phone': self.qikberry_session_id.to_contact
                    })
                else :
                    partner.write({'name':'XXXXX'})

            opportunity = self.env['crm.lead'].sudo().create({
                'type': 'opportunity',
                'name': partner_id.name + "'s Opportunity" if partner_id else self.qikberry_session_id.name,
                'partner_id': self.partner_id.id if self.partner_action == 'exist' and self.partner_id else partner_id.id if partner_id else False,
                'qikberry_session_id': self.qikberry_session_id.id,
                'phone': partner_id.phone if partner_id else self.qikberry_session_id.to_contact,
                'lead_source_id': lead_source.id if lead_source else False,
                'user_id': self.user_id.id if self.user_id else False,
                # 'team_id': self.team_id.id if self.team_id else False,
            })
            self.qikberry_session_id.opportunity_id = opportunity.id
            print("-----------", self.qikberry_session_id.opportunity_id,"-----self.qikberry_session_id.opportunity_id------\n")
            return {
                'name': 'Opportunity',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead',
                'view_mode': 'form',
                'res_id': opportunity.id if opportunity else False,
                'target': 'current'
            }



class ExistingOpportunityLine(models.TransientModel):
    _name = 'existing.haboo_qikberry.opportunity.line'

    wizard_id = fields.Many2one('haboo_qikberry.opportunity.convert.wizard', string='Wizard')
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity')