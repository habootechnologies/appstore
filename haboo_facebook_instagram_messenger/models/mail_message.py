import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class Message(models.Model):
    _inherit = "mail.message"

    message_type = fields.Selection(
        selection_add=[
            ("insta_msgs", "Instagram Msgs"),
            ("facebook_msgs", "Facebook Msgs"),
        ],
        ondelete={
            "insta_msgs": lambda recs: recs.write({"insta_msgs": "odoo"}),
            "facebook_msgs": lambda recs: recs.write({"facebook_msgs": "odoo"}),
        },
    )

    isFbMsgs = fields.Boolean("FB msgs")
    isInstaMsgs = fields.Boolean("Insta msgs")

    @api.model_create_multi
    def create(self, values_list):
        provider_id = False
        messages = super(Message, self).create(values_list)

        if self.env.context:
            for values in values_list:
                model = self.env[values.get('model')].browse(values.get('res_id'))
                is_discuss = model._name == 'discuss.channel' and (model.facebook_channel or model.instagram_channel) or False
                if values.get("message_type") in ["facebook_msgs", "insta_msgs"] or is_discuss:
                    if model.facebook_channel:
                        values['message_type'] = 'facebook_msgs'
                    elif model.instagram_channel:
                        values['message_type'] = 'insta_msgs'
                    vals = {}
                    user = self.env.user
                    if "user_id" in self.env.context and self.env.context.get(
                        "user_id"
                    ):
                        user = self.env.context.get("user_id")
                    if user.id != self.env.ref("base.public_user").id:
                        if values.get("model") == "discuss.channel":
                            channel_company_line_id = self.env[
                                "messenger.channel.provider.line"
                            ].search([("channel_id", "=", message.res_id)])
                            # phone change to mobile
                            if channel_company_line_id:
                                # social_media_id = channel_company_line_id.partner_id.mobile.social_media_id('+').replace(' ', '')
                                if channel_company_line_id.messenger_provider_id:
                                    provider_id = (
                                        channel_company_line_id.messenger_provider_id
                                    )

                                # Multi Companies and Multi Providers Code Here
                                if provider_id:
                                    vals = {
                                        "provider_id": provider_id.id,
                                        "author_id": user.partner_id.id,
                                        "message": values.get("body", "").replace(
                                            "<br/>", "\n"
                                        ),
                                        "type": "in queue",
                                        "partner_id": channel_company_line_id.partner_id.id,
                                        "attachment_ids": values.get("attachment_ids"),
                                        "model": self._context.get(
                                            "active_model", "discuss.channel"
                                        ),
                                    }
                                    if values.get("message_type") == "facebook_msgs":
                                        vals.update(
                                            {
                                                "account_id": channel_company_line_id.partner_id.messenger_account_id,
                                            }
                                        )
                                    elif values.get("message_type") == "insta_msgs":
                                        vals.update(
                                            {
                                                "account_id": channel_company_line_id.partner_id.instagram_account_id,
                                            }
                                        )
                                    # if 'user_id' in self.env.context and self.env.context.get('user_id'):
                                    #     vals.update({'provider_id': self.env.context.get('user_id').provider_id.id})
                                else:
                                    raise AccessError(_("Please add provider in User!"))

                        else:
                            partner = False
                            data = (
                                self.env[values.get("model")]
                                .sudo()
                                .search_read([("id", "=", int(values.get("res_id")))])
                            )
                            if values.get("model") == "res.partner":
                                partner = self.env["res.partner"].browse(data[0]["id"])
                            elif "partner_id" in data[0]:
                                if data[0]["partner_id"]:
                                    partner = self.env["res.partner"].browse(
                                        data[0]["partner_id"][0]
                                    )
                                else:
                                    raise AccessError(
                                        _(
                                            "Partner must be Required for instagram/messenger message!"
                                        )
                                    )
                            else:
                                raise AccessError(
                                    _(
                                        "Partner must be Required for instagram/messenger message!"
                                    )
                                )

                            if partner:

                                # Multi Companies and Multi Providers Code Here
                                provider_id = user.messenger_provider_id
                                if provider_id:
                                    provider_channel_id = partner.messenger_channel_provider_line_ids.filtered(
                                        lambda s: s.messenger_provider_id == provider_id
                                    )
                                else:
                                    raise AccessError(_("Please add provider in User!"))
                                user_partner = user.partner_id
                                part_lst = [partner.id, user_partner.id]

                                if provider_channel_id:
                                    channel = provider_channel_id.channel_id

                                    if (
                                        user_partner.id
                                        not in channel.channel_partner_ids.ids
                                    ):
                                        channel.sudo().write(
                                            {
                                                "channel_partner_ids": [
                                                    (4, user_partner.id)
                                                ]
                                            }
                                        )
                                else:
                                    channel = False
                                    if values.get("message_type") == "facebook_msgs":
                                        name = partner.messenger_account_id
                                        channel = self.env["discuss.channel"].create(
                                            {
                                                # 'public': 'public',
                                                "channel_type": "chat",
                                                "email_send": False,
                                                "name": name,
                                                "facebook_channel": True,
                                                "channel_partner_ids": part_lst,
                                            }
                                        )
                                    if values.get("message_type") == "insta_msgs":
                                        name = partner.instagram_account_id
                                        channel = self.env["discuss.channel"].create(
                                            {
                                                # 'public': 'public',
                                                "channel_type": "chat",
                                                "email_send": False,
                                                "name": name,
                                                "instagram_channel": True,
                                                "channel_partner_ids": part_lst,
                                            }
                                        )
                                    channel.write(
                                        {
                                            "channel_member_ids": [(5, 0, 0)]
                                            + [
                                                (0, 0, {"partner_id": line_vals})
                                                for line_vals in part_lst
                                            ]
                                        }
                                    )
                                    # Multi Companies and Multi Providers Code Here
                                    if (
                                        provider_id
                                        and user.id
                                        == self.env.ref("base.public_user").id
                                    ):
                                        partner.write(
                                            {
                                                "messenger_channel_provider_line_ids": [
                                                    (
                                                        0,
                                                        0,
                                                        {
                                                            "channel_id": channel.id,
                                                            "messenger_provider_id": provider_id.id,
                                                        },
                                                    )
                                                ]
                                            }
                                        )
                                    else:
                                        raise AccessError(
                                            _("Please add provider in User!")
                                        )

                                message_values = {
                                    "body": values.get("body", ""),
                                    "author_id": user_partner.id,
                                    "email_from": user_partner.email or "",
                                    "model": values.get("model"),
                                    "message_type": "comment",
                                    "subtype_id": self.env["ir.model.data"]
                                    .sudo()
                                    ._xmlid_to_res_id("mail.mt_comment"),
                                    # 'channel_ids': [(4, channel.id)],
                                    "partner_ids": [(4, user_partner.id)],
                                    "res_id": values.get("res_id"),
                                    "reply_to": user_partner.email,
                                }

                                if values.get("attachment_ids"):
                                    message_values.update(
                                        {"attachment_ids": values.get("attachment_ids")}
                                    )
                                message_comment = (
                                    self.env["mail.message"]
                                    .sudo()
                                    .create(message_values)
                                )
                                notifications = channel._channel_message_notifications(
                                    message_comment
                                )
                                self.env["bus.bus"]._sendmany(notifications)
                                # Multi Companies and Multi Providers Code Here
                                if provider_id:
                                    vals = {
                                        "provider_id": provider_id.id,
                                        "author_id": user.partner_id.id,
                                        "message": values.get("body", ""),
                                        "type": "in queue",
                                        "partner_id": partner.id,
                                        "attachment_ids": values.get("attachment_ids"),
                                        "model": self._context.get(
                                            "active_model", "discuss.channel"
                                        ),
                                    }
                                    if values.get("message_type") == "facebook_msgs":
                                        vals.update(
                                            {
                                                "account_id": partner.messenger_account_id,
                                            }
                                        )
                                    elif values.get("message_type") == "insta_msgs":
                                        vals.update(
                                            {
                                                "account_id": partner.instagram_account_id,
                                            }
                                        )
                                else:
                                    raise AccessError(_("Please add provider in User!"))

                                for mes in messages:
                                    mes.model = "discuss.channel"
                                    mes.res_id = channel.id
                                    mes.chatter_wa_model = (values.get("model"),)
                                    mes.chatter_wa_res_id = values.get("res_id")
                                    mes.chatter_wa_message_id = message_comment.id
                                    mes.chatter_wa_model = mes.chatter_wa_model.split(
                                        "'"
                                    )[1]
                                    # mes.channel_ids = [(4,channel.id)]

                        if "company_id" in self.env.context:
                            vals.update(
                                {"company_id": self.env.context.get("company_id")}
                            )

                        if message.message_id:
                            vals.update({"message_id": values.get("message_id")})

                        if self.env.context.get("whatsapp_application"):
                            if values.get("message_type") == "facebook_msgs":
                                self.env["messenger.history"].sudo().with_context(
                                    {"whatsapp_application": True}
                                ).create(vals)
                            if values.get("message_type") == "insta_msgs":
                                self.env["instagram.history"].sudo().with_context(
                                    {"whatsapp_application": True}
                                ).create(vals)

                        if (
                            message.parent_id
                            and not self.env.context.get("whatsapp_application")
                            and self.env.context.get("message") != "received"
                        ):
                            if values.get("message_type") == "facebook_msgs":
                                self.env["messenger.history"].sudo().with_context(
                                    {
                                        "wa_messsage_id": message,
                                        "message_parent_id": message.parent_id,
                                    }
                                ).create(vals)
                            if values.get("message_type") == "insta_msgs":
                                self.env["instagram.history"].sudo().with_context(
                                    {
                                        "wa_messsage_id": message,
                                        "message_parent_id": message.parent_id,
                                    }
                                ).create(vals)

                        if (
                            not message.parent_id
                            and not self.env.context.get("whatsapp_application")
                            and self.env.context.get("message") != "received"
                            and not self.env.context.get("template_send")
                        ):
                            if values.get("message_type") == "facebook_msgs":
                                self.env["messenger.history"].sudo().with_context(
                                    {"message_id": message}
                                ).create(vals)
                            if values.get("message_type") == "insta_msgs":
                                self.env["instagram.history"].sudo().with_context(
                                    {"message_id": message}
                                ).create(vals)

                        if self.env.context.get("template_send"):
                            dicto = {
                                "wa_messsage_id": message,
                                "template_send": True,
                                "wa_template": self.env.context.get("wa_template"),
                                "attachment_ids": self.env.context.get(
                                    "attachment_ids"
                                ),
                                "active_model_id": self.env.context.get(
                                    "active_model_id"
                                ),
                            }

                            if (
                                "active_model_id_chat_bot" in self.env.context
                                and "active_model_chat_bot" in self.env.context
                            ):
                                dicto.update(
                                    {
                                        "active_model_id_chat_bot": self.env.context.get(
                                            "active_model_id_chat_bot"
                                        ),
                                        "active_model_chat_bot": self.env.context.get(
                                            "active_model_chat_bot"
                                        ),
                                    }
                                )
                            if values.get("message_type") == "facebook_msgs":
                                self.env[
                                    "messenger.history"
                                ].sudo().with_context().create(vals)
                            if values.get("message_type") == "insta_msgs":
                                self.env[
                                    "instagram.history"
                                ].sudo().with_context().create(vals)
        return messages
