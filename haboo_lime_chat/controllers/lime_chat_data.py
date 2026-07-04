from odoo import http
from odoo.http import request
import json
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class LimeChatWebhook(http.Controller):

    @http.route('/webhook/haboo_lime_chat',type='json',auth='public',methods=['POST'],csrf=False)
    def lime_chat_webhook(self, **kw):
        data = json.loads(request.httprequest.data.decode('utf-8'))
        _logger.info("-----------", data,"-----data------\n")
        token = data.get('token')
        expected = request.env['ir.config_parameter'].sudo().get_param('haboo_lime_chat.api.token')
        if token != expected:
            return {"status": "error", "message": "Invalid token!"}
        haboo_lime_chat = request.env['lime.chat'].sudo().create({
            'field_one': data.get('text_1'),
            'field_two': data.get('text_2'),
            'field_three': data.get('text_3'),
            'field_four': data.get('text_4'),
            'field_five': data.get('text_5')
        })
        _logger.info("data.get('text_1')",data.get('text_1'))
        _logger.info("data.get('text_1')",data.get('text_2'))
        _logger.info("data.get('text_1')",data.get('text_3'))
        _logger.info("data.get('text_1')",data.get('text_4'))
        _logger.info("lime",haboo_lime_chat.field_one)
        return {
            "status": "success",
            "id": haboo_lime_chat.id,
        }
