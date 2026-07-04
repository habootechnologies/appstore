from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LimeChat(models.Model):
    _name = 'lime.chat'
    _description = 'Lime Chat'

    field_one = fields.Char(string='Field One')
    field_two = fields.Char(string='Field Two')
    field_three = fields.Char(string='Field Three')
    field_four = fields.Char(string='Field Four')
    field_five = fields.Char(string='Field Five')

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    partner_name = fields.Char(string='Partner Name')
    partner_email = fields.Char(string='Partner Email')
    partner_phone = fields.Char(string='Partner Phone')

    opportunity_id = fields.Many2one(
        'crm.lead', string='Opportunity', readonly=True, copy=False,
    )
    is_converted = fields.Boolean(
        string='Converted to Opportunity', default=False, readonly=True, copy=False,
    )

    def action_convert_to_opportunity(self):
        """Open the convert to opportunity wizard."""
        self.ensure_one()
        if self.is_converted:
            raise UserError(_('This chat has already been converted to an opportunity.'))

        # Try to find existing partner by email or phone
        partner = False
        if self.partner_email:
            partner = self.env['res.partner'].search([
                ('email', '=', self.partner_email)
            ], limit=1)
        if not partner and self.partner_phone:
            partner = self.env['res.partner'].search([
                ('phone', '=', self.partner_phone)
            ], limit=1)

        # Find existing opportunities for the link option
        or_conditions = []
        if self.partner_email:
            or_conditions.append(('email_from', '=', self.partner_email))
        if self.partner_phone:
            or_conditions.append(('phone', '=', self.partner_phone))
        if self.partner_name:
            or_conditions.append(('partner_name', '=', self.partner_name))
        if partner:
            or_conditions.append(('partner_id', '=', partner.id))

        if or_conditions:
            or_domain = ['|'] * (len(or_conditions) - 1) + or_conditions
            existing_opportunities = self.env['crm.lead'].search(or_domain, limit=50)
        else:
            # No match criteria — load all active opportunities
            existing_opportunities = self.env['crm.lead'].search([], limit=50)

        # Build One2many line vals
        line_vals = []
        for opp in existing_opportunities:
            line_vals.append((0, 0, {
                'opportunity_id': opp.id,
            }))

        wizard = self.env['lime.chat.convert.opportunity'].create({
            'lime_chat_id': self.id,
            'partner_id': partner.id if partner else False,
            'name': self.name or self.partner_name or 'New Opportunity',
            'partner_name': self.partner_name or '',
            'email_from': self.partner_email or '',
            'phone': self.partner_phone or '',
            'description': self.description or '',
            'action': 'exist' if partner else 'create',
            'convert_type': 'create',
            'line_ids': line_vals,
        })

        return {
            'name': _('Convert to Opportunity'),
            'type': 'ir.actions.act_window',
            'res_model': 'lime.chat.convert.opportunity',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': self.env.context,
        }

    def action_view_opportunity(self):
        """Open the linked opportunity."""
        self.ensure_one()
        if not self.opportunity_id:
            raise UserError(_('No opportunity linked to this chat.'))
        return {
            'name': _('Opportunity'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'res_id': self.opportunity_id.id,
            'target': 'current',
        }
