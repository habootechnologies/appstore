
from future.backports.datetime import timedelta
from odoo import models, fields, api
import requests
import json
import shopify
from datetime import date, datetime, time
import base64
import pytz
from dateutil import parser  # Import dateutil to handle timezone-aware strings





class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopify_order_id = fields.Char()
    from_shopify = fields.Boolean()
    fulfillment_status = fields.Selection([('fulfilled','Fulfilled'),('unfulfilled','Unfulfilled')],string='Fulfillment Status')
    updated_date = fields.Datetime()
    note = fields.Char()
    tracking = fields.Char()
    tracking_url = fields.Text()

    def get_shopify_connection(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_api_key', False)
        access_token =self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_access_token', False)
        shop_name = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_shop_name', False)
        version=self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_version', False)

        shop_url =f"https://{api_key}:{access_token}@{shop_name}.myshopify.com/admin/api/{version}"
        shopify.ShopifyResource.set_site(shop_url)
        print("Connected to Shopify API.")

    def _update_shopify_order_history_data(self, limit=100):
        self.get_shopify_connection()
        get_next_page = True
        since_id = 0
        today_str_from = datetime.combine(datetime.today(), time.min)
        today_str_to = datetime.combine(datetime.today(), time.max)
        today_date = date.today()
        yesterday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        print("--------", yesterday,"----yesterday---\n")

        # today_str_from = (today_str_from - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        # today_str_to = (today_str_to - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        print("-----------", today_str_from,"-----today_str_from------\n")
        print("-----------", today_str_to,"-----today_str_to------\n")
        while get_next_page:
            orders = shopify.Order.find(limit=limit,since_id=since_id,updated_at_min="2025-09-06 00:00:00",updated_at_max="2025-09-08 23:59:59",status="any")
            # orders = shopify.Order.find(limit=limit,since_id=since_id,updated_at_min=f"{today_date} 00:00:00",updated_at_max=f"{today_date} 23:59:59",status="any")
            # print(f"Fetching orders since_id={since_id}, limit={limit}")
            # orders = shopify.Order.find(status="any",limit=limit,created_at_min="2025-03-03 00:00:00",created_at_max="2025-03-03 23:59:59",since_id=since_id)
            # print("-----------", orders, "-----orders------\n")

            if not orders:
                # print("No more orders to fetch.")
                break

            for order in orders:
                # print("-----------", order,"-----order------\n")
                # print("-----------", type(order), "-----order------\n")
            # print(f"Fetching orders since_id={since_id}, limit={limit}")
                customer_data = order.customer if hasattr(order, 'customer') else {}
                default_address = order.default_address if hasattr(order, 'default_address') else {}
                # print("-----------", customer_data, "-----customer_data------\n")

                sale_order_partner = False
                if customer_data:
                    sale_order_partner = self.env['res.partner'].search(
                        [('shopify_customer_id', '=', customer_data.id)], limit=1)
                # print("-----------", customer_data,"-----customer_data------\n")

                if not sale_order_partner:
                    create_date = customer_data.created_at if hasattr(customer_data, 'created_at') else None
                    if create_date is not None:
                        cre_date = datetime.strptime(create_date, '%Y-%m-%dT%H:%M:%S%z').date()
                        str_cre = str(cre_date)
                    if customer_data and hasattr(customer_data, 'default_address'):
                        phone = customer_data.default_address.phone if customer_data.default_address and customer_data.default_address.phone else None
                    else:
                        phone = None
                    modify_date = customer_data.updated_at if hasattr(customer_data, 'updated_at') else None
                    address = customer_data.default_address if customer_data and hasattr(customer_data,
                                                                                         'default_address') and customer_data.default_address else None

                    street = getattr(address, 'address1', '') if address else ''
                    street2 = getattr(address, 'address2', '') if address else ''
                    state_id = False
                    country_id=False
                    # phone=address.phone if address and hasattr(address, 'phone')  else ' '
                    # print("-----------", phone,"-----phone------\n")
                    if address and hasattr(address, 'province'):
                        state_name = address.province
                        state_record = self.env['res.country.state'].search([('name', '=', state_name)], limit=1)
                        state_id = state_record.id if state_record else False

                    if address and hasattr(address, 'country'):
                        country_name = address.country
                        country_record = self.env['res.country'].search([('name', '=', country_name)], limit=1)
                        country_id = country_record.id if country_record else False


                    city = address.city if address and hasattr(address, 'city') else ''
                    values = {
                        'shopify_customer_id': customer_data.id if hasattr(customer_data, 'id') else '',
                        'name': f"{customer_data.first_name} {customer_data.last_name}" if hasattr(customer_data,'first_name') or hasattr(customer_data, 'last_name') else '',
                        'street': street,
                        'street2': street2,
                        'state_id': state_id if state_id else False,
                         'created_date': create_date,
                        'modified_date':modify_date,
                        'city': city,
                        'country_id':country_id if country_id else False,
                        'email': customer_data.email if hasattr(customer_data, 'email') else '',
                        'phone': phone,
                        'from_shopify': True,
                    }
                    sale_order_partner=self.env['res.partner'].create(values)
                created_at_dt = datetime.strptime(order.created_at, "%Y-%m-%dT%H:%M:%S%z")
                created_at_date = created_at_dt.astimezone(pytz.utc).replace(tzinfo=None)
                note = order.cancel_reason

                update_at_date = None
                if order.closed_at:
                    update_at_dt = datetime.strptime(order.closed_at, "%Y-%m-%dT%H:%M:%S%z")
                    update_at_date = update_at_dt.astimezone(pytz.utc).replace(tzinfo=None)
                tracking_numbers = ""
                if order.fulfillments:
                    tracking_numbers = order.fulfillments[0].tracking_number if order.fulfillments else ''
                tracking_url =""
                if order.fulfillments:
                    tracking_url = order.fulfillments[0].tracking_url if order.fulfillments else ''

                sale_order_values = {
                    'fulfillment_status':'fulfilled' if order.fulfillment_status == 'fulfilled' else 'unfulfilled',
                    'shopify_order_id':order.id,
                    'name': order.name,
                    'date_order': created_at_date,
                    'updated_date':update_at_date,
                    'partner_id': sale_order_partner.id,
                    'currency_id': self.env['res.currency'].search([('name', '=', order.currency)], limit=1).id,
                    'order_line': [],
                    'state': 'sale',
                    'note':order.cancel_reason if order.cancel_reason else None,
                    'tracking':tracking_numbers if tracking_numbers else None,
                    'tracking_url':tracking_url if tracking_url else None,
                    'from_shopify':True,
                }


                for item in order.line_items:
                    product_id = item.product_id if hasattr(item, 'product_id') else None

                    if not product_id:
                        continue


                    product = self.env['product.product'].search([('product_id', '=', product_id)], limit=1)
                    if not product:
                        product_values = {
                            'name': item.title,
                            'default_code': item.sku if item.sku else '',
                            'product_id': product_id,
                            'list_price': float(item.price) if hasattr(item, 'price') else 0.0,
                        }
                        product = self.env['product.product'].create(product_values)

                    existing_product_ids = {line.product_id for line in order.line_items}

                    if product.id in existing_product_ids:
                        print(f"Skipping duplicate product: {product.id}")
                        continue  # Skip adding duplicate lines

                    line_item_values = {
                        'product_id': product.id,
                        'name': item.title if hasattr(item, 'title') else '',
                        'product_uom': 1,
                        'fulfillment_status':'Fulfilled' if item.fulfillment_status == 'fulfilled' else 'null',
                        'product_uom_qty': item.quantity if hasattr(item, 'quantity') else 1,
                        'price_unit': float(item.price) if hasattr(item, 'price') else 0.0,
                        # 'price_subtotal': item.amount if hasattr(item, 'amount') else 0.0,
                        # 'tax_id': tax_id if tax_id else False,

                    }
                    # if None in line_item_values.values() or line_item_values['product_id'] is False:
                    #     print(f"Skipping invalid line item: {line_item_values}")
                    #     continue

                    sale_order_values['order_line'].append((0, 0, line_item_values))
                if order.total_shipping_price_set:
                    shipping_amount = order.total_shipping_price_set.shop_money.amount
                    if float(shipping_amount) > 0:
                        shipping_product = self.env['product.template'].search([('is_shipping_product', '=', True)], limit=1)
                        if shipping_product:
                            shipping_item_values = {
                                'product_id': shipping_product.id,
                                'name': 'Shipping Charges',
                                'product_uom': 1,
                                'product_uom_qty': 1,
                                'price_unit': float(shipping_amount),
                            }
                            sale_order_values['order_line'].append((0, 0, shipping_item_values))
                if not sale_order_values['partner_id']:
                    print("Error: partner_id is required in sale_order_values.")
                    continue
                exisiting_order = self.env['sale.order'].search([('name', '=', sale_order_values['name'])], limit=1)

                if not exisiting_order:
                    created_sale_order=self.env['sale.order'].create(sale_order_values)
                    self.env.cr.commit()
                    opportunity_id = self.env['crm.lead'].search([('shopify_order_no','=',sale_order_values['name'])],limit=1)
                    if opportunity_id:
                        created_sale_order.write({'opportunity_id': opportunity_id.id})
                    print("--------", 1111111111111111111111,"----1111111111111111111111---\n")


                else:

                    existing_product_ids = {line.product_id.id for line in exisiting_order.order_line}

                    new_order_lines = [line for line in sale_order_values['order_line'] if
                                       line[2].get('product_id') not in existing_product_ids]
                    update_fields = {}
                    if exisiting_order.fulfillment_status != sale_order_values.get('fulfillment_status'):
                        update_fields['fulfillment_status'] = sale_order_values.get('fulfillment_status')
                    if exisiting_order.tracking != sale_order_values.get('tracking'):
                        update_fields['tracking'] = sale_order_values.get('tracking')
                    if exisiting_order.tracking_url != sale_order_values.get('tracking_url'):
                        update_fields['tracking_url'] = sale_order_values.get('tracking_url')
                    if new_order_lines:
                        update_fields['order_line'] = new_order_lines
                    if update_fields:
                        exisiting_order.write(update_fields)
                    # else:
                    #     print("No new lines or updates, skipping.")
            if len(orders) < limit:
                get_next_page = False
                print("Fetched all available orders.")
            else:
                since_id = orders[-1].id
                print("--------", since_id,"----since_id---\n")





    def find_tax_for_product(self, line_item=None):
        tax_list = []
        if line_item:
            for tax_line in line_item.get("tax_lines"):
                rate = tax_line.get("rate") * 100
                name = "{} {}%".format(tax_line.get("title"), int(rate))
                tax_id = self.env["account.tax"].search(
                    [("name", "=", name), ("amount", "=", rate), ("amount_type", "=", "percent"),
                     ("type_tax_use", "=", "sale")], limit=1)
                if not tax_id:
                    tax_group_id = self.env["account.tax.group"].search([("name", "=", tax_line.get("title"))], limit=1)
                    if not tax_group_id:
                        tax_group_id = self.env["account.tax.group"].create({"name": tax_line.get("title")})
                    tax_id = self.env["account.tax"].create({"name": name,
                                                             "amount": rate,
                                                             "amount_type": "percent",
                                                             "type_tax_use": "sale",
                                                             "tax_group_id": tax_group_id.id,
                                                             "description": name
                                                             })
                tax_list.append(tax_id.id)
        return tax_list










