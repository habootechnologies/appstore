from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LimeChatConvertOpportunity(models.TransientModel):
    _name = 'lime.chat.convert.opportunity'
    _description = 'Convert Lime Chat to Opportunity'

    lime_chat_id = fields.Many2one('lime.chat', string='Lime Chat', required=True, readonly=True)

    # ---- Convert Type: Create New or Link Existing ----
    convert_type = fields.Selection([
        ('create', 'Create a New Opportunity'),
        ('link', 'Link to an Existing Opportunity'),
    ], string='Action', required=True, default='create')

    # ---- One2many lines with existing opportunities (each line has a Link button) ----
    line_ids = fields.One2many(
        'lime.chat.convert.opportunity.line', 'wizard_id',
        string='Existing Opportunities',
    )

    # ---- Fields for creating new opportunity ----
    name = fields.Char(string='Opportunity Name')
    description = fields.Text(string='Description')
    email_from = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    partner_name = fields.Char(string='Customer Name')

    action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
        ('nothing', 'Do not link to a customer'),
    ], string='Customer', default='create')

    partner_id = fields.Many2one('res.partner', string='Customer')
    team_id = fields.Many2one('crm.team', string='Sales Team')
    user_id = fields.Many2one(
        'res.users', string='Salesperson', default=lambda self: self.env.user,
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='0')

    @api.onchange('action')
    def _onchange_action(self):
        if self.action != 'exist':
            self.partner_id = False

    def action_create_opportunity(self):
        """Create a new opportunity from the lime chat."""
        self.ensure_one()
        haboo_lime_chat = self.lime_chat_id
        lead_source = self.env['lead.source.config'].search([('code', '=', 'LIMECHAT')], limit=1)

        if haboo_lime_chat.is_converted:
            raise UserError(_('This chat has already been converted to an opportunity.'))

        if not self.name:
            raise UserError(_('Please enter an opportunity name.'))

        # Handle partner creation / linking
        partner_id = False
        if self.action == 'create':
            partner = self.env['res.partner'].create({
                'name': self.partner_name or self.name,
                'email': self.email_from,
                'phone': self.phone,
            })
            partner_id = partner.id
        elif self.action == 'exist':
            if not self.partner_id:
                raise UserError(_('Please select an existing customer.'))
            partner_id = self.partner_id.id

        lead_vals = {
            'name': self.name,
            'partner_id': partner_id,
            'contact_name': self.partner_name,
            'email_from': self.email_from,
            'phone': self.phone,
            'description': self.description,
            'team_id': self.team_id.id if self.team_id else False,
            'user_id': self.user_id.id if self.user_id else False,
            'priority': self.priority,
            'type': 'opportunity',
            'lead_source_id': lead_source.id if lead_source else False,

        }
        lead = self.env['crm.lead'].create(lead_vals)

        haboo_lime_chat.write({
            'opportunity_id': lead.id,
            'is_converted': True,
        })

        return {
            'name': _('Opportunity'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': lead.id,
            'target': 'current',
        }


class LimeChatConvertOpportunityLine(models.TransientModel):
    _name = 'lime.chat.convert.opportunity.line'
    _description = 'Convert Lime Chat to Opportunity Line'

    wizard_id = fields.Many2one(
        'lime.chat.convert.opportunity', string='Wizard', required=True, ondelete='cascade',
    )
    opportunity_id = fields.Many2one('crm.lead', string='Opportunity', readonly=True)

    # Related fields from crm.lead for display in tree
    partner_id = fields.Many2one(related='opportunity_id.partner_id', string='Customer', readonly=True)
    email_from = fields.Char(related='opportunity_id.email_from', string='Email', readonly=True)
    phone = fields.Char(related='opportunity_id.phone', string='Phone', readonly=True)
    stage_id = fields.Many2one(related='opportunity_id.stage_id', string='Stage', readonly=True)
    user_id = fields.Many2one(related='opportunity_id.user_id', string='Salesperson', readonly=True)

    def button_link(self):
        """Link the lime chat to this opportunity and close the wizard."""
        self.ensure_one()
        haboo_lime_chat = self.wizard_id.lime_chat_id
        lead_source = self.env['lead.source.config'].search([('code', '=', 'LIMECHAT')], limit=1)


        if haboo_lime_chat.is_converted:
            raise UserError(_('This chat has already been converted to an opportunity.'))

        # Check if this lime chat is already linked to another opportunity
        existing = self.env['lime.chat'].search([
            ('opportunity_id', '=', self.opportunity_id.id),
            ('id', '!=', haboo_lime_chat.id),
        ], limit=1)
        if existing:
            raise UserError(
                _('This Opportunity is already linked to another Lime Chat - %s') % existing.name
            )

        lead = self.opportunity_id

        # Update lead with chat info if lead fields are empty
        update_vals = {}
        if not lead.email_from and haboo_lime_chat.partner_email:
            update_vals['email_from'] = haboo_lime_chat.partner_email
        if not lead.phone and haboo_lime_chat.partner_phone:
            update_vals['phone'] = haboo_lime_chat.partner_phone
        if not lead.contact_name and haboo_lime_chat.partner_name:
            update_vals['contact_name'] = haboo_lime_chat.partner_name
        if update_vals:
            lead.write(update_vals)

        haboo_lime_chat.write({
            'opportunity_id': lead.id,
            'is_converted': True,

        })

        return {'type': 'ir.actions.act_window_close'}
