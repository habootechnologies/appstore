from odoo import fields, models


class MailChannel(models.Model):
    _inherit = "mail.channel"

    instagram_channel = fields.Boolean(string="Instagram Channel")
    facebook_channel = fields.Boolean(string="Facebook Channel")
    
    def channel_info(self):
        """ facebook_channel and instagram_channel fields sent in JS
        """
        channel_infos = super().channel_info()
        channel_infos_dict = dict((c['id'], c) for c in channel_infos)
        for channel in self:
            channel_infos_dict[channel.id]['channel']['instagram_channel'] = channel.instagram_channel
            channel_infos_dict[channel.id]['channel']['facebook_channel'] = channel.facebook_channel
            is_tus_discuss_installed = self.env['ir.module.module'].sudo().search(
                [('state', '=', 'installed'), ('name', '=', 'tus_meta_wa_discuss')])
            if is_tus_discuss_installed:
                if channel.instagram_channel or channel.facebook_channel:
                    channel_infos_dict[channel.id]['channel']['whatsapp_channel'] = channel.whatsapp_channel
        return list(channel_infos_dict.values())
