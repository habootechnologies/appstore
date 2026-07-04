# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # shopify_product_access_url= fields.Char(string='Shopify Product Access URL',config_parameter='haboo_shopify_integration.shopify_product_access_url')
    # shopify_customer_access_url= fields.Char(string='Shopify Customer Access URL',config_parameter='haboo_shopify_integration.shopify_customer_access_url')
    # shopify_order_access_url= fields.Char(string='Shopify Order Access URL',config_parameter='haboo_shopify_integration.shopify_order_access_url')
    shopify_access_token = fields.Char(string='Shopify Access Token',config_parameter='haboo_shopify_integration.shopify_access_token')
    shopify_api_key = fields.Char(config_parameter='haboo_shopify_integration.shopify_api_key')
    shopify_shop_name = fields.Char(config_parameter='haboo_shopify_integration.shopify_shop_name')
    shopify_version = fields.Char(config_parameter='haboo_shopify_integration.shopify_version')



