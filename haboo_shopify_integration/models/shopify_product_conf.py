from odoo import models, fields, api
import requests
import json
from datetime import date, datetime, time
from odoo.exceptions import UserError, MissingError
import shopify
import base64


class productTemplate(models.Model):
    _inherit = 'product.template'

    # product_tmpl_id = fields.Many2one('product.template')
    shopify_product_id = fields.Char()
    product_id= fields.Char(string='Product ID')
    tile = fields.Char(string='Product Title')
    vendor = fields.Char(string='Vendor')
    created_at= fields.Datetime(string='Created At')
    status = fields.Char(string='Status')
    sku=fields.Char()
    uom_id=fields.Many2one('uom.uom')
    from_shopify = fields.Boolean()

    # product_category = fields.Many2one(related='product_tmpl_id.categ_id')

    def get_shopify_connection(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_api_key', False)
        access_token = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_access_token',
                                                                        False)
        shop_name = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_shop_name', False)
        version = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_version', False)

        shop_url = f"https://{api_key}:{access_token}@{shop_name}.myshopify.com/admin/api/{version}"
        # shop_url = "https://<api_key>:<access_token>@<your-store>.myshopify.com/admin/api/2024-07"
        shopify.ShopifyResource.set_site(shop_url)
        print("Connected to Shopify API.")


    def _update_shopify_product_history_data(self, limit=100):
        self.get_shopify_connection()
        get_next_page = True
        since_id = 0
        today_str_from = datetime.combine(datetime.today(), time.min).strftime("%Y-%m-%d %H:%M:%S")
        today_str_to = datetime.combine(datetime.today(), time.max).strftime("%Y-%m-%d %H:%M:%S")
        today_date = date.today()


        while get_next_page:
            print(f"Fetching products since_id={since_id}, limit={limit}")
            products = shopify.Product.find(since_id=since_id, limit=limit,updated_at_min="2025-04-28 00:00:00",updated_at_max="2025-05-01 23:59:59")

            if not products:
                print("No more products to fetch.")
                break

            for product in products:
                values = {
                    'product_id': product.id,
                    'name': product.title,
                    # 'detailed_type': 'product',
                    'categ_id': 1,
                    'uom_id': 1,
                    'uom_po_id': 1,
                    'status': product.status,
                    'default_code': product.variants[0].sku if product.variants else '',
                    'list_price': product.variants[0].price if product.variants else '',
                    'image_1920': product.images[0].src if product.images else '',
                    'sale_line_warn': 'no-message',
                    'from_shopify':True,
                    # 'tracking': 'none',
                    # 'purchase_line_warn': 'no-message',
                }
                if product.images:
                    image_url = product.images[0].src
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        values['image_1920'] = base64.b64encode(response.content).decode('utf-8')
                    else:
                        values['image_1920'] = False
                        print(f"Failed to fetch image from {image_url}")
                else:
                    values['image_1920'] = False
                existing_product = self.env['product.template'].search([('default_code', '=', values['default_code'])],
                                                                       limit=1)
                if not existing_product:
                        self.env['product.template'].create(values)
                        print(f"Created new product: {values['name']} (ID: {values['product_id']}  (default_code: {values['default_code']})")

                else:
                    existing_product.write(values)
                    print(f"Updated existing product: {values['list_price']} (ID: {values['product_id']}) (default_code: {values['default_code']})")
                self.env.cr.commit()

            if len(products) < limit:
                get_next_page = False
                print("Fetched all available products.")
            else:
                since_id = products[-1].id

       














