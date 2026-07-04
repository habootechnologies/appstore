from odoo import models, fields, api,_
import requests
import json
import base64
import mimetypes
from odoo.exceptions import ValidationError,UserError
import logging
from datetime import date, datetime, time


_logger = logging.getLogger(__name__)



class QikChatMessage(models.Model):
    _name = "qikchat.message"
    _description = "QikChat Message Status"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    message_id = fields.Char(string="Message ID")
    to_contact = fields.Char(string="To Contact")
    name = fields.Char(string="Contact Name")
    status = fields.Char(string="Delivery Status")
    sent_at = fields.Datetime(string="Sent At")
    delivered_at = fields.Datetime(string="Delivered At")
    read_at = fields.Datetime(string="Read At")
    processed_at = fields.Datetime(string="Processed At")
    last_updated_at = fields.Datetime(string="Last Updated At")
    state = fields.Selection([('new', 'New'), ('running', 'Running'),
                              ('close', 'Closed')], default="new", store=True)
    running_date = fields.Datetime()
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    send_message = fields.Text(string='Send Message')
    product_image = fields.Binary('Image', attachment=True, help="filed to store image")
    file_name = fields.Char(string="File Name")
    create_date = fields.Datetime(default=datetime.today())


    def start_session(self):
        self.state = 'running'
        self.running_date = fields.Datetime.now()

    def close_session(self):
        self.state = 'close'

    def qikberry_create_opportunity_wizard(self):
        partner_new = False
        existing_opportunities = False
        partner = self.env['res.partner'].search([('phone', '=', self.to_contact)], limit=1)
        print("-----------", partner,"-----partner------\n")
        if not partner:
            partner_new = self.env['res.partner'].create({
                'name': self.name or "XXXXXXX",
                'phone': self.to_contact,
            })
        if partner:
            existing_opportunities = self.env['crm.lead'].search([('partner_id', '=', partner.id)])
            print("-----------", existing_opportunities,"-----existing_opportunities------\n")
        self.state = 'close'
        return {
            'name': 'Convert to Opportunity',
            'type': 'ir.actions.act_window',
            'res_model':'haboo_qikberry.opportunity.convert.wizard',
            'view_mode': 'form',
            'context': {
                'default_qikberry_session_id': self.id,
                'default_conversion_action': 'merge' if existing_opportunities else 'convert',
                'default_user_id': self.env.user.id,
                'default_partner_action': 'exist' if partner else 'create',
                'default_partner_id': partner.id if partner else partner_new,
                'default_opportunity_ids': existing_opportunities.ids if existing_opportunities else False,
            },
            'target': 'new',

        }

    def _get_file_type(self):
        """Determine if the uploaded file is an image or a document"""
        if not self.file_name:
            return "document"

        file_type, _ = mimetypes.guess_type(self.file_name)
        if file_type and file_type.startswith("image/"):
            return "image"
        return "document"

        # ---------------------------------------------------------
        # 2️⃣ Send the file (image or document) to QikChat
        # ---------------------------------------------------------

    def _send_to_qikchat(self, file_url, file_type):
        qikchat_url = "https://api.qikchat.in/v1/messages"
        api_key = "YuuB-EopQ-NRsZ"  # 🔑 replace with your valid key

        headers = {
            "Content-Type": "application/json",
            "QIKCHAT-API-KEY": api_key,
        }

        if file_type == "image":
            payload = {
                "to_contact": self.to_contact,
                "type": "image",
                "image": {
                    "link": file_url,
                    "caption": "🖼️ Image",
                },
            }
        else:
            payload = {
                "to_contact": self.to_contact,
                "type": "document",
                "document": {
                    "link": file_url,
                    "caption": "📄 Document",
                    "filename": self.file_name or "odoo_document.pdf",
                },
            }

        _logger.info("Sending QikChat %s payload: %s", file_type, payload)
        response = requests.post(qikchat_url, headers=headers, json=payload, timeout=30)

        if response.status_code not in [200, 201]:
            raise ValidationError(f"{file_type.capitalize()} sending failed: {response.text}")

        return response.json()

        # ---------------------------------------------------------
        # 3️⃣ Prepare public URL and send
        # ---------------------------------------------------------

    def _prepare_send_media(self):
        """Prepare Odoo public URL and send image/document"""
        if not self.product_image:
            raise ValidationError("Please upload a file before sending.")



        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # Create a public attachment
        attachment = self.env['ir.attachment'].sudo().create({
            'name': self.file_name or 'odoo_file',
            'datas': self.product_image,
            'res_model': self._name,
            'res_id': self.id,
            'public': True,
        })

        # 🔁 Commit to ensure it's available to external fetchers like Qikberry
        self.env.cr.commit()
        base_url = base_url.replace('http://', 'https://', 1)

        file_url = f"{base_url}/web/content/{attachment.id}?download=true"
        print("\n---------", file_url, "-----------file_url---------\n")
        file_type = self._get_file_type()
        _logger.info("✅ Generated public %s URL for QikChat: %s", file_type, file_url)

        # ✅ Retry accessibility check (Qikberry sometimes too fast)
        for attempt in range(3):
            try:
                test_response = requests.head(file_url, timeout=5)
                if test_response.status_code in [200, 302]:
                    break
                _logger.warning("⚠️ Attempt %s: file not yet accessible (%s)", attempt + 1, file_url)
            except Exception as e:
                _logger.warning("⚠️ Attempt %s: accessibility check failed: %s", attempt + 1, e)

        # ✅ Send to QikChat
        response_data = self._send_to_qikchat(file_url, file_type)
        _logger.info(f"✅ {file_type.capitalize()} sent to {self.to_contact}: {response_data}")
        return True

        # ---------------------------------------------------------
        # 4️⃣ Send text + optional media
        # ---------------------------------------------------------

    def action_send_message(self):
        qikchat_url = "https://api.qikchat.in/v1/messages"
        api_key = "YuuB-EopQ-NRsZ"

        headers = {
            "Content-Type": "application/json",
            "QIKCHAT-API-KEY": api_key,
        }

        # ✅ Send text first
        if self.send_message:
            payload = {
                "to_contact": self.to_contact,
                "type": "text",
                "preview_url": True,
                "text": {"body": self.send_message},
            }

            _logger.info("Sending QikChat text payload: %s", payload)
            response = requests.post(qikchat_url, headers=headers, json=payload, timeout=30)

            if response.status_code not in [200, 201]:
                raise ValidationError(f"Message sending failed: {response.text}")

            response_json = response.json()
            _logger.info("✅ Text message sent to %s: %s", self.to_contact, response_json)

            self.message_post(body=self.send_message)
            self.write({'send_message': ''})

        # ✅ Send file if available
        if self.product_image:
            self._prepare_send_media()

        return True





