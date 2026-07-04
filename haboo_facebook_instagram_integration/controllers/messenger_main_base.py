import base64
import json
import requests
from odoo import http, _
from odoo.http import request
from datetime import datetime, timedelta, timezone
import logging
_logger = logging.getLogger(__name__)

class WebHook3(http.Controller):
    _webhook_url = "/graph_api/webhook"
    _meta_fb_url = "/graph_api/webhook"

    @http.route('/dropzone/upload', type='json', auth='user', methods=['POST'], csrf=False)
    def upload_file(self, **kwargs):
        data = json.loads(request.httprequest.data.decode("utf-8"))
        filename = data["params"].get("filename")
        mimetype = data["params"].get("mimetype")
        file_data = data["params"].get("datas")
        thread = data["params"].get("thread")
        model = data["params"].get("model")
        file = data["params"].get("file")
        # file = data["params"].get("file")
        response = False
        if filename and mimetype and file_data and model == 'tata.whatsapp.session':
            response = self.send_dropimage_whatsup(filename, file_data, mimetype, thread)
            return response.status_code
        return 200

    @http.route('/meta/test', type='http', auth='public', methods=['POST'], csrf=False)
    def meta_messages_test_webhook(self, **kw):
        user_id = request.env.user
        user = request.env['res.users']
        if user_id:
            user = request.env['res.users'].sudo().browse(user_id.id)
        channel = "meta_channel"

        data = json.loads(request.httprequest.data.decode("utf-8"))
        ref_message = {
            "data": data,
            "channel": channel
        }
        message = "<b>Test</b>"
        request.env["bus.bus"]._sendone(
            user.partner_id,
            'simple_notification', {
                'title': _("Need Quotation Approval"),
                'message_is_html': message,
                "message": message,
                'sticky': False,
                'warning': True,
            })
        
        existing_session = request.env['messenger.session'].sudo().search([], limit=1)
        
        message_rec = request.env['mail.message'].sudo().create({
            "message_type": 'comment', 
            'model': 'messenger.session', 
            'res_id': existing_session.id, 
            "body": data.get('name', '')
        })

        # if message_rec:
        #     self.create_mail_notification(message_rec)

        _logger.info("before bus===============")

        request.env["bus.bus"]._sendone(channel, "notification", ref_message)
        _logger.info("After bus===============")

    # @http.route('/send/meta/message', type='json', auth='user', methods=['POST'], csrf=False)
    # def send_message(self, **kwargs):
    #     data = kwargs
    #     message_code = None
    #     attachment_code = []

    #     message_body = data.get("body", "")
    #     attachment_ids = data.get("attachment_ids", [])
    #     partner_ids = data.get("partner_ids", [])
    #     model = data.get("model", "")
    #     res_id = data.get("res_id", 0)

    #     messenger_session_id = request.env['messenger.session'].sudo().browse(res_id)
        
    #     if message_body:
    #         message_value = messenger_session_id.action_send_message_controller(message_body)
    #         message_code = message_value
    #         try:
    #             print("message_code response:", message_value.status_code, message_value.json())
    #         except Exception as e:
    #             print("Could not parse message response:", e)

    #     if attachment_ids:
    #         return_value = messenger_session_id.send_attachment_using_url_controller(attachment_ids)
    #         attachment_code = return_value
    #         print("attachment_code:", attachment_code)

    #     return message_code.status_code if message_code else False, attachment_code

    @http.route('/send/meta/message', type='json', auth='user', methods=['POST'], csrf=False)
    def send_message(self, **kwargs):
        data = kwargs
        message_code = None
        attachment_results = []

        message_body = data.get("body", "")
        attachment_ids = data.get("attachment_ids", [])
        res_id = data.get("res_id", 0)

        # print("\n=== Incoming Meta Message Request ===")
        # print("Request Data:", data)

        messenger_session_id = request.env['messenger.session'].sudo().browse(res_id)
        # print("Messenger Session:", messenger_session_id)

        # Send text message if exists
        if message_body:
            print("\nSending message body:", message_body)
            try:
                message_value = messenger_session_id.action_send_message_controller(message_body)
                if hasattr(message_value, 'status_code'):
                    message_code = message_value.status_code
                elif isinstance(message_value, dict) and 'status_code' in message_value:
                    message_code = message_value.get('status_code')
                else:
                    message_code = None
                # print("Message Send Raw Response:", message_value)
                # print("Extracted Message Status Code:", message_code)
            except Exception as e:
                # print("Error sending message:", e)
                message_code = 500

        # Send attachments
        if attachment_ids:
            # print("\nAttachments to send:", attachment_ids)
            for attachment_id in attachment_ids:
                try:
                    # print(f"Sending Attachment ID: {attachment_id}")
                    result = messenger_session_id.send_attachment_using_url_controller([attachment_id])
                    # print(f"Raw Attachment Response for ID {attachment_id}:", result)

                    status_code = 500  # Default to fail
                    # Handle multiple possible formats
                    if isinstance(result, list) and len(result) > 0:
                        # If first element has status_code
                        first_response = result[0]
                        if hasattr(first_response, 'status_code'):
                            status_code = first_response.status_code
                    elif hasattr(result, 'status_code'):
                        status_code = result.status_code
                    elif isinstance(result, dict) and 'status_code' in result:
                        status_code = result.get('status_code')

                    attachment_results.append({
                        'id': attachment_id,
                        'status': status_code,
                    })
                    # print(f"Attachment {attachment_id} processed with status:", status_code)
                except Exception as e:
                    # print(f"Error sending attachment {attachment_id}:", e)
                    attachment_results.append({
                        'id': attachment_id,
                        'status': 500,
                        'error': str(e),
                    })

        response_data = {
            'message_status': message_code,
            'attachments': attachment_results
        }
        # print("\n=== Final Response to Frontend ===")
        print(response_data)

        return response_data

    @http.route(_webhook_url, type="http", methods=["GET"], auth="public", csrf=False)
    def facebook_webhook(self, **kw):
        # _logger.info("facebook_webhook called=====================")
        # print("facebook_webhook called=====================")
        if kw.get("hub.verify_token"):
            # _logger.info("facebook_webhook called=====================%s", kw.get("hub.verify_token"))
            # print("facebook_webhook called=====================%s", kw.get("hub.verify_token"))
            return kw.get("hub.challenge")

    def _get_messenger_received_attachment(self, message_obj, provider):
        attachment_value = {}
        media_url = message_obj.get("attachments")[0].get("payload").get("url")
        if message_obj.get("attachments")[0].get("type") == 'image':
            attachment_value.update({'name': 'messenger_image',
                                     'type': 'binary',
                                     'mimetype': 'image/jpeg'})
        elif message_obj.get("attachments")[0].get("type") == 'video':
            attachment_value.update({"name": "messenger_video",
                                     "type": "binary",
                                     "mimetype": "video/mp4"})
        elif message_obj.get("attachments")[0].get("type") == 'file':
            attachment_value.update({"name": "messenger_file",
                                     "type": "binary",
                                     "mimetype": "application/pdf"})
        elif message_obj.get("attachments")[0].get("type") == 'audio':
            attachment_value.update({"name": "messenger_audio",
                                     "type": "binary",
                                     "mimetype": "audio/mpeg"})
        elif message_obj.get("attachments")[0].get("type") == 'share':
            attachment_value.update({"name": "messenger_insta_shared",
                                     "type": "binary"})
        elif message_obj.get("attachments")[0].get("type") == 'ig_reel':
            attachment_value.update({"name": "insta_ig_reel",
                                     "type": "binary",
                                     "mimetype": "video/mp4"})
        if media_url:
            decoded = self.get_media_data(media_url, provider)
            attachment_value.update({'datas': decoded})
            attachment = request.env['ir.attachment'].sudo().create(attachment_value)
            return attachment

    def get_media_data(self, url, provider):
        payload = {}
        headers = {"Authorization": "Bearer " + provider.graph_api_token}
        response = requests.request("GET", url, headers=headers, data=payload)
        decoded = base64.b64encode(response.content)
        return decoded

    @http.route(
        _meta_fb_url, type="json", methods=["GET", "POST"], auth="public", csrf=False
    )
    def messenger_meta_webhook(self, **kw):
        # _logger.info("messenger_meta_webhook called=====================")
        # print("messenger_meta_webhook called=====================")
        wa_dict = {}

        data = json.loads(request.httprequest.data.decode("utf-8"))
        # _logger.info("data called=====================%s", data)
        print("data=======ssssssssssssssssssss==", data)
        print("\n\n\n\n ooooooooooooooooooooooooooooooooooooooooooooooooo\n\n\n")
        wa_dict.update({"messages": data.get("messages")})
        if data.get("object") == "instagram":
            provider = request.env["provider"].sudo().search([("graph_api_authenticated", "=", True), 
                                                            ('instagram_business_account_id', '=', data.get('entry')[0].get('id')),
                                                            ('meta_platform', '=', 'instagram')], limit=1)
            if not provider:
                provider = request.env["provider"].sudo().search(
                    [("graph_api_authenticated", "=", True),
                     ('instagram_business_account_id', '=', data.get('entry')[0].get('id'))], limit=1)
        else:
            provider = request.env["provider"].sudo().search(
                [("graph_api_authenticated", "=", True), '|', ("account_id", '=', data.get('entry')[0].get('id')),
                 ('instagram_business_account_id', '=', data.get('entry')[0].get('id'))], limit=1)

        # _logger.info("provider called=====================%s", provider)
        # print("provider called=====================", provider)

        wa_dict.update({"provider": provider})
        if provider.graph_api_authenticated:
            user_partner = provider.user_id.partner_id
            if data.get("entry") and data.get("entry")[0].get("messaging") and data.get("entry")[0].get("messaging")[0].get("message"):
                message = data.get("entry")[0].get("messaging")[0].get("message")
                page_id = data.get("entry")[0].get("messaging")[0].get("sender").get("id")
                messages_id = data.get("entry")[0].get("messaging")[0].get("message").get("mid")
            elif data.get("entry") and data.get("entry")[0].get("standby") and data.get("entry")[0].get("standby")[0].get("message"):
                message = data.get("entry")[0].get("standby")[0].get("message")
                page_id = data.get("entry")[0].get("standby")[0].get("sender").get("id")
                messages_id = data.get("entry")[0].get('standby')[0].get('message').get('mid')
            else:
                message = False
                page_id = False
                messages_id = False
            if message and page_id and messages_id:
                wa_dict.update({"chat": True})
                partners = False
                if data.get("object") in ["page", "instagram"]:
                    platform = 'instagram' if data.get("object") == 'instagram' else 'messenger'
                    partners = request.env["res.partner"].sudo().search(
                        ['|', ("messenger_account_id", "=", page_id), ("instagram_account_id", "=", page_id)])
                    # print("partners============", partners)
                    # _logger.info("partners partners====================%s", partners)
                    wa_dict.update({"partners": partners})
                    if not partners:
                        user_conversation_url = "%s%s/conversations?platform=%s&user_id=%s&access_token=%s" % (
                            provider.graph_api_url, provider.account_id, platform, page_id, provider.graph_api_token)
                        user_conversations_requests = requests.get(user_conversation_url)
                        # print("user_conversations_requests------------------", user_conversations_requests)
                        # _logger.info("user_conversations_requests------------------%s", user_conversations_requests)
                        
                        user_conversations_datas = user_conversations_requests.json()
                        # print("user_conversations_datas------------------", user_conversations_datas)
                        if user_conversations_datas.get("data"):
                            # print("user_conversations_datas.get("")==============", user_conversations_datas.get("data"))
                            # _logger.info("user_conversations_datas.get----------------%s", user_conversations_datas.get("data"))
                            messages_url = "%s%s?fields=messages&access_token=%s" % (
                                provider.graph_api_url, user_conversations_datas.get("data")[0].get("id"),
                                provider.graph_api_token,)
                            messages_requests = requests.get(messages_url)
                            messages_datas = messages_requests.json()
                            # print("messages_datas.get("")==============", messages_datas)
                            # _logger.info("messages_datas.get-----------------%s", messages_datas)
                            if messages_datas.get("messages").get("data"):
                                users_messages_url = "%s%s?fields=to,from,message&access_token=%s" % (
                                    provider.graph_api_url, messages_datas.get("messages").get("data")[0].get("id"),
                                    provider.graph_api_token)
                                user_messages_requests = requests.get(users_messages_url)
                                user_messages_datas = user_messages_requests.json()
                                # print("user_messages_datas===========", user_messages_datas)
                                if user_messages_datas.get("to") and user_messages_datas.get("to").get("data")[0].get(
                                        'id') == provider.account_id:
                                    user_name = user_messages_datas.get("from").get("name")
                                    user_account_id = user_messages_datas.get("from").get("id")
                                    user_email = user_messages_datas.get("from").get("email")

                                elif user_messages_datas.get("from") and user_messages_datas.get("from").get(
                                        'id') == provider.account_id:
                                    user_name = user_messages_datas.get("to").get("data")[0].get('name')
                                    user_account_id = user_messages_datas.get("to").get("data")[0].get('id')
                                    user_email = user_messages_datas.get("to").get("data")[0].get('email')
                                elif platform == 'instagram':
                                    user_name = user_messages_datas.get("from").get("username")
                                    user_account_id = user_messages_datas.get("from").get("id")
                                    user_email = user_messages_datas.get("from").get("email")
                                else:
                                    user_name = ""
                                    user_email = ""
                                    user_account_id = ""
                                partners = request.env["res.partner"].sudo().create({
                                    "name": user_name,
                                    "email": user_email,
                                })
                                if data.get("object") == 'page':
                                    partners.sudo().write({
                                        "messenger_account_id": user_account_id
                                    })
                                elif data.get("object") == 'instagram':
                                    partners.sudo().write({
                                        "instagram_account_id": user_account_id
                                    })
                for partner in partners:
                    vals = {}
                    if message.get("text"):
                        vals.update({
                            "message": message.get("text"),
                        })

                    elif message.get("attachments")[0].get("type") in ["image", "video", "file", "audio", "share", "ig_reel"]:
                        attachment = self._get_messenger_received_attachment(message, provider)
                        vals.update({
                            "message": message.get("attachments")[0].get("payload").get('title') if message.get("attachments")[0].get("payload").get('title') else '',
                            'attachment_ids': [(4, attachment.id)],
                        })
                    elif message.get("attachments")[0].get("type") == 'fallback':
                        attachment_value = {"name": "messenger_fallback",
                                            "type": "url",
                                            'url': message.get("attachments")[0].get("payload").get("url")}
                        attachment = request.env['ir.attachment'].sudo().create(attachment_value)
                        vals.update({
                            "message": message.get("attachments")[0].get("payload").get('title') if
                            message.get("attachments")[0].get("payload").get('title') else '',
                            'attachment_ids': [(4, attachment.id)],
                        })

                    check_record = request.env['messenger.session'].sudo().search([('sender_id', '=', page_id)])
                    # print("check_record================", check_record)
                    # _logger.info("check_record.get-----------------%s", check_record)
                    if not check_record:
                        val = {
                            "provider_id": provider.id,
                            "partner_id": partner.id,
                            "sender_id": page_id,
                            "company_id": provider.company_id.id,
                        }
                        if val:
                            check_record = request.env["messenger.session"].sudo().create(val)
                    # print("message==============", message)
                    # _logger.info("message.message-----------------%s", message)
                    # print("message_id==============", messages_id)
                    request.env["messenger.messages"].sudo().create({
                        "session_id" : check_record.id,
                        "message_text" : message,
                        "message_id" : messages_id,
                        "attachment_ids" : vals.get('attachment_ids'),
                        })
                    # print("check_record================", request.env["messenger.messages"].sudo().search([('session_id', '=', check_record.id)]))
                    
                    channel = "meta_channel"
                    ref_message = {
                        "data": message,
                        "channel": channel
                    }
                    request.env["bus.bus"]._sendone(
                        user_partner,
                        'simple_notification', {
                            'title': _("New Message"),
                            'message_is_html': message.get('text') if message.get('text') else False,
                            "message": message.get('text') if message.get('text') else False,
                            'sticky': False,
                            'warning': True,
                        })
                    message_rec = request.env['mail.message'].sudo().create({
                        "message_type": 'auto_comment', 
                        'model': 'messenger.session', 
                        'author_id': partner.id, 
                        'res_id': check_record.id, 
                        "body": message.get('text') if message.get('text') else message.get('attachments')[0].get('type'),
                        "attachment_ids" : vals.get('attachment_ids'),
                    })

                    # if message_rec:
                    #     self.create_mail_notification(message_rec, partner)
                    # request.env["bus.bus"]._sendone(channel, "notification", message.get('text'))
                    request.env["bus.bus"]._sendone(channel, "notification", ref_message)
            self.instagram_comment_webhook(**kw)
        return wa_dict

    def instagram_comment_webhook(self, **kw):
        """
        Handles Instagram comment and reply events for ALL posts.
        Even if a post is not fetched into Odoo, it auto-creates it.
        """
        try:
            data = json.loads(request.httprequest.data.decode("utf-8"))

            # 🕒 Convert UNIX timestamp to human-readable IST format
            for entry in data.get("entry", []):
                unix_time = entry.get("time")
                if unix_time:
                    try:
                        ist_time = datetime.fromtimestamp(int(unix_time), tz=timezone.utc) + timedelta(hours=5, minutes=30)
                        entry["time"] = ist_time.strftime("%d/%m/%Y %H:%M:%S")
                    except Exception as inner_e:
                        _logger.warning("⚠️ Failed to convert entry time: %s", inner_e)

            _logger.info("📥 Incoming Instagram Webhook (real-time): %s", json.dumps(data, indent=2))

        except Exception as e:
            _logger.warning("⚠️ Invalid JSON in webhook: %s", e)
            return {"status": "invalid_json"}

        if data.get("object") not in ["instagram", "page"]:
            return {"status": "ignored"}
        comment_from = data.get("object")
        print("MYYYYY", data)
        for entry in data.get("entry", []):
            entry_time = entry.get("time")
            for change in entry.get("changes", []):
                field = change.get("field")
                value = change.get("value", {})
                print(field, value)
                if field == "comments" or field == "feed":
                    self._handle_comment(value, entry_time, comment_from)
                elif field == "comment_replies":
                    self._handle_reply(value, entry_time, comment_from)
                return {"status": "ok"}

    def _handle_facebook_comment(self, value, entry_time=None):
        value.get("comment_id")
        username = value.get("from", {}).get("name", "Unknown")
        message = value.get("message", "")
        comment_id = value.get("comment_id", "")
        post_id =  value.get("post_id", "")
        item_id = value.get("item", "")
        verb_id =  value.get("verb", "")
        post_value = value.get("post", "")
        timestamp = datetime.now()
        if item_id == "comment":
            comment= request.env['post.comments'].sudo().search([('comment_id', '=', comment_id)], limit=1)
            if verb_id == "remove" and comment:
                comment.sudo().unlink()
            if verb_id == "add":
                account = request.env["provider"].sudo().search([
                    ('graph_api_authenticated', '=', True),
                    ('meta_platform', '=', "facebook")
                ], limit=1)
                post = request.env['post.post'].sudo().search([('post_id', '=', post_id)])
                if account and not post:
                    post_url =   f"https://graph.facebook.com/v24.0/{post_id}"
                    params = {
                        'fields': 'id,permalink_url,from,attachments,message,actions',
                        'access_token': account.graph_api_token,
                    }
                    response = requests.get(post_url, params=params, timeout=60)
                    data = response.json()
                    post_username = ''
                    if data.get('from'):
                        post_username = data.get('from').get('name', '')
                    attachment_data = data.get('attachments').get('data')[0]
                    media = attachment_data.get('media',)
                    image = media.get('image', '')
                    data_to_write = {
                        'post_id': post_id,
                        'meta_platform': "facebook",
                        'permalink': data.get('permalink_url', ''),
                        'username': post_username,
                        'media_type': attachment_data.get('type', ''),
                        'media_url': image.get('src', ''),
                        'caption': data.get('message', '')
                        }
                    post = request.env['post.post'].sudo().create(data_to_write)
                vals = {
                    "post_id": post.id,
                    "comment_id": comment_id,
                    "username": username,
                    "text": message,
                    "timestamp": timestamp,
                }
                if comment:
                    comment.write(vals)
                else:
                    comment = request.env['post.comments'].sudo().create(vals)
        return True

    def _handle_comment(self, value, entry_time=None, comment_from=None):
        """Process a new Instagram comment and notify users."""
        if comment_from == 'page':
            return self._handle_facebook_comment(value=value, entry_time=entry_time)
        comment_id = value.get("id")
        text = value.get("text", "")
        username = value.get("from", {}).get("username", "Unknown")
        media_id = value.get("media", {}).get("id")
        timestamp = datetime.now()
        _logger.info("💬 New comment %s by %s: %s", comment_id, username, text)
        Post = request.env["post.post"].sudo()
        post = Post.search([("post_id", "=", media_id)], limit=1)
        url = f"https://graph.facebook.com/v24.0/"
        provider = False
        if comment_from == "instagram":
            url = f"https://graph.instagram.com/v24.0/"
            provider = request.env["provider"].sudo().search(
                [("graph_api_authenticated", "=", True), ("meta_platform", "=", "instagram")],
                limit=1,
            )
        else:
            provider = request.env["provider"].sudo().search([("graph_api_authenticated", "=", True), ("meta_platform", "=", "facebook")], limit=1)
        if not post and media_id:
            if provider:
                url = url + str(media_id)
                params = {
                    "fields": "id,caption,media_url,media_type,permalink,timestamp,username",
                    "access_token": provider.graph_api_token,
                }
                resp = requests.get(url, params=params)
                if resp.status_code == 200:
                    media = resp.json()
                    post = Post.create({
                        "post_id": media.get("id"),
                        "caption": media.get("caption"),
                        "media_url": media.get("media_url"),
                        "media_type": media.get("media_type"),
                        "timestamp": media.get("timestamp"),
                        "permalink": media.get("permalink"),
                        "username": media.get("username"),
                    })
                else:
                    _logger.warning("⚠️ Could not fetch post %s: %s", media_id, resp.text)
                    post = Post.create({"post_id": media_id, "caption": "Auto-created (fetch failed)"})
            else:
                _logger.warning("⚠️ No provider found, creating post locally")
                post = Post.create({"post_id": media_id, "caption": "Auto-created (no provider)"})

        # Add or update comment
        Comment = request.env["post.comments"].sudo()
        comment = Comment.search([("comment_id", "=", comment_id)], limit=1)
        vals = {
            "post_id": post.id,
            "comment_id": comment_id,
            "username": username,
            "text": text,
            "timestamp": timestamp,
        }
        if comment:
            comment.write(vals)
        else:
            comment = Comment.create(vals)
        # Move post to top of list (update timestamp)
        post.write({"latest_comment_timestamp": timestamp})
        title_notification = f"💬 New {comment_from} Comment "
        # Send Odoo notification
        message_html = f"<b>{username}</b> commented: {text}<br/><i>on post: {post.post_id}</i>"
        for user in request.env["res.users"].sudo().search([]):
            request.env["bus.bus"]._sendone(
                user.partner_id,
                "simple_notification",
                {
                    "title": title_notification,
                    "message_is_html": True,
                    "message": message_html,
                    "sticky": False,
                },
            )
        _logger.info("✅ Comment notification sent for %s", comment_id)

    def _handle_reply(self, value, entry_time=None, comment_from=None):
        """Handles replies to comments."""
        reply_id = value.get("id")
        text = value.get("text", "")
        username = value.get("from", {}).get("username", "Unknown")
        _logger.info("↩️ Reply %s by %s: %s", reply_id, username, text)
        request.env["mail.message"].sudo().create({
            "message_type": "comment",
            "model": "post.comments",
            "res_id": 1,
            "body": f"<b>{username}</b> replied: {text}",
        })








    # def create_mail_notification(self, message_rec, notify_partner_id):
    #     notif_create_values = [{
    #         'author_id': message_rec.author_id.id,
    #         'mail_message_id': message_rec.id,
    #         'res_partner_id': notify_partner_id.id,
    #         'notification_type': 'sms',
    #         'notification_status': 'sent',
    #     }]
    #     request.env['mail.notification'].sudo().create(notif_create_values)
    #     return True

    # @http.route('/send/meta/message', type='json', auth='user', methods=['POST'], csrf=False)
    # def send_message(self, **kwargs):
    #     data = kwargs
    #     attachment_code = False
    #     message_code = False
    #     message_body = data.get("body", "")
    #     attachment_ids = data.get("attachment_ids", [])
    #     print("attachment_ids============", attachment_ids)
    #     partner_ids = data.get("partner_ids", [])
    #     model = data.get("model", "")
    #     res_id = data.get("res_id", 0)
    #     messenger_session_id = request.env['messenger.session'].search([('id', '=', res_id)])
    #     if message_body:
    #         message_value = messenger_session_id.action_send_message_controller(message_body)
    #         message_code = message_value
    #     if attachment_ids:
    #         return_value = messenger_session_id.send_attachment_using_url_controller(attachment_ids)
    #         attachment_code = return_value
    #     print("message_code==========", message_code, message_code.json())
    #     print("attachment_code==========", attachment_code)
    #     return message_code.status_code if message_code else False, attachment_code.status_code if attachment_code else False
