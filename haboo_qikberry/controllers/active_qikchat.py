from odoo import http, _
from odoo.http import request, Response
import json
import logging
from datetime import datetime
import requests
import base64

_logger = logging.getLogger(__name__)

class QikchatWebhookController(http.Controller):

    @http.route('/qikchat/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def qikchat_webhook(self, **kwargs):
        try:
            raw_data = request.httprequest.data.decode("utf-8")
            data = json.loads(raw_data or '{}')
            print("=========== Incoming Qikchat Webhook ===========")
            print("----------- Raw Data:", data, "-----------\n")

            event_type = data.get('event')
            payload = data.get('payload', {})
            if not event_type and data.get('message'):
                event_type = data['message'].get('event')
                payload = data['message'].get('payload', {})

            if event_type != 'whatsapp:message:in':
                print(f"⚠️ Ignored event: {event_type}")
                return http.Response("Ignored non-incoming event", status=200)

            # Extract message info
            contacts = payload.get('contacts', [{}])[0]
            msg_info = payload.get('message', {})
            message_type = msg_info.get('type')
            print("📨 Incoming Message Type:", message_type)

            message_text = '-'
            attachment_id = False

            # Identify sender
            phone_number = contacts.get('to')
            if not phone_number:
                return http.Response("Missing phone number", status=400)

            partner_name = contacts.get('profile', {}).get('name', 'Unknown')

            # ✅ Find or create partner
            partner = request.env['res.partner'].sudo().search([('phone', '=', phone_number)], limit=1)
            if not partner:
                partner = request.env['res.partner'].sudo().create({
                    'name': partner_name,
                    'phone': phone_number
                })
                print("🧾 Created new partner:", partner.name)

            # ✅ Find or create chat session
            QikChat = request.env['qikchat.message'].sudo()
            existing_session = QikChat.search([('to_contact', '=', phone_number)], limit=1)

            if not existing_session:
                vals = {
                    'message_id': payload.get('id'),
                    'to_contact': phone_number,
                    'name': partner_name,
                    'status': message_type,
                    'sent_at': msg_info.get('timestamp'),
                    'processed_at': msg_info.get('timestamp'),
                    'last_updated_at': msg_info.get('timestamp'),
                }
                for f in ['sent_at', 'processed_at', 'last_updated_at']:
                    if vals.get(f):
                        try:
                            vals[f] = datetime.strptime(vals[f], '%Y-%m-%dT%H:%M:%S.%fZ')
                        except Exception:
                            pass

                existing_session = QikChat.create(vals)
                print("🆕 New chat created:", existing_session.id)
            else:
                if payload.get('id') and existing_session.message_id != payload.get('id'):
                    existing_session.write({'message_id': payload.get('id')})
                existing_session.write({'status': message_type})
                print(f"🔁 Updated existing chat: {existing_session.id}")

            # ✅ TEXT MESSAGE
            if message_type == 'text':
                message_text = msg_info.get('text', {}).get('body', '')

            # ✅ IMAGE MESSAGE
            elif message_type == 'image':
                image_info = msg_info.get('image', {})
                image_url = image_info.get('url')
                mime_type = image_info.get('mime_type', 'image/jpeg')
                message_text = "<p><b>📷 Image received:</b></p>"

                if image_url:
                    try:
                        res = requests.get(image_url, timeout=10)
                        if res.status_code == 200:
                            attachment = request.env['ir.attachment'].sudo().create({
                                'name': image_url.split('/')[-1],
                                'datas': base64.b64encode(res.content),
                                'res_model': 'qikchat.message',
                                'res_id': existing_session.id,   # ✅ Correct link to record
                                'type': 'binary',
                                'mimetype': mime_type,
                            })
                            attachment_id = attachment.id
                            print("✅ Image attached:", attachment.id)
                    except Exception as e:
                        print("❌ Image download error:", e)

            # ✅ STICKER MESSAGE
            elif message_type == 'sticker':
                sticker_info = msg_info.get('sticker', {})
                sticker_url = sticker_info.get('url')
                mime_type = sticker_info.get('mime_type', 'image/webp')
                message_text = (
                    f"<p>🩵 <b>Sticker:</b> <a href='{sticker_url}' target='_blank'>{sticker_url}</a></p>"
                    f"<img src='{sticker_url}' width='100' style='margin-top:5px;'/>"
                )

                if sticker_url:
                    try:
                        res = requests.get(sticker_url, timeout=10)
                        if res.status_code == 200:
                            attachment = request.env['ir.attachment'].sudo().create({
                                'name': sticker_url.split('/')[-1],
                                'datas': base64.b64encode(res.content),
                                'res_model': 'qikchat.message',
                                'res_id': existing_session.id,   # ✅ Link for user access
                                'type': 'binary',
                                'mimetype': mime_type,
                            })
                            attachment_id = attachment.id
                            print("✅ Sticker attached:", attachment.id)
                    except Exception as e:
                        print("❌ Sticker download error:", e)

            # ✅ VIDEO MESSAGE
            elif message_type == 'video':
                video_info = msg_info.get('video', {})
                video_url = video_info.get('url')
                mime_type = video_info.get('mime_type', 'video/mp4')
                message_text = (
                    f"<p>🎥 <b>Video:</b> <a href='{video_url}' target='_blank'>{video_url}</a></p>"
                    f"<video controls width='300' style='margin-top:5px; border-radius:8px;'>"
                    f"<source src='{video_url}' type='{mime_type}'>"
                    f"Your browser does not support the video tag."
                    f"</video>"
                )

                if video_url:
                    try:
                        res = requests.get(video_url, timeout=10)
                        if res.status_code == 200:
                            attachment = request.env['ir.attachment'].sudo().create({
                                'name': video_url.split('/')[-1],
                                'datas': base64.b64encode(res.content),
                                'res_model': 'qikchat.message',
                                'res_id': existing_session.id,   # ✅ Proper link
                                'type': 'binary',
                                'mimetype': mime_type,
                            })
                            attachment_id = attachment.id
                            print("✅ Video attached:", attachment.id)
                    except Exception as e:
                        print("❌ Video download error:", e)

            # ✅ AUDIO MESSAGE
            elif message_type == 'audio':
                audio_info = msg_info.get('audio', {})
                audio_url = audio_info.get('url')
                mime_type = audio_info.get('mime_type', 'audio/ogg; codecs=opus')
                message_text = (
                    f"<p>🎧 <b>Voice message received:</b> "
                    f"<a href='{audio_url}' target='_blank'>{audio_url}</a></p>"
                    f"<audio controls src='{audio_url}' style='margin-top:5px;'></audio>"
                )

            # ✅ REACTION MESSAGE
            elif message_type == 'reaction':
                reaction_info = msg_info.get('reaction', {})
                emoji = reaction_info.get('emoji')
                reacted_to = reaction_info.get('message_id', 'unknown')
                message_text = f"<p>💬 Reacted to message <code>{reacted_to}</code> with <b>{emoji}</b></p>"
                print("✅ Reaction:", emoji)

            else:
                message_text = f"[{message_type}]"

            print("📩 Message Text:", message_text)

            # ✅ Post message in chatter
            mail_message_vals = {
                'author_id': partner.id if partner else False,
                'message_type': 'comment',
                'model': 'qikchat.message',
                'res_id': existing_session.id,
                'body': message_text or '-',
            }

            if attachment_id:
                mail_message_vals['attachment_ids'] = [(6, 0, [attachment_id])]

            request.env['mail.message'].sudo().create(mail_message_vals)
            print("💬 Message logged in chatter")

            return http.Response("Message logged successfully", status=200)

        except Exception as e:
            _logger.exception("❌ Error in Qikchat webhook: %s", e)
            return http.Response("Error processing webhook", status=500)
