from numpy.core.records import record
from odoo import models, fields, api
import requests
import shopify
import json
from datetime import date, datetime, time
import base64


class ResPartner(models.Model):
    _inherit = 'res.partner'

    shopify_customer_id = fields.Char(string='Shopify Customer', store = True )
    from_shopify = fields.Boolean()

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

    def _update_shopify_customer_data(self,limit=100):
        self.get_shopify_connection()
        get_next_page = True
        since_id = 0
        today_str_from = datetime.combine(datetime.today(), time.min).strftime("%Y-%m-%d %H:%M:%S")
        today_str_to = datetime.combine(datetime.today(), time.max).strftime("%Y-%m-%d %H:%M:%S")
        while get_next_page:
            print(f"Fetching customers since_id={since_id}, limit={limit}")
            customers = shopify.Customer.find(since_id=since_id, limit=limit,created_at_min=today_str_from,created_at_max=today_str_to,updated_at_min=today_str_from,updated_at_max=today_str_to)
            print("-----------", customers,"-----customers------\n")

        

            if not customers:
                print("No more customers to fetch.")
                break
            for customer in customers:
                create_date = customer.created_at if hasattr(customer,'created_at') else None
                print("-----------", type(create_date),"-----type(create_date)------\n")    
                cre_date = datetime.strptime(create_date, '%Y-%m-%dT%H:%M:%S%z').date()
                str_cre =str(cre_date)
                print("-----------", str_cre,"-----str_cre------\n")
                # shopify_customer_id = customer.id if hasattr(customer,'id') else ''
                phone = customer.phone if hasattr(customer, 'phone') else ''
                # create_date = customer.created_at if hasattr(customer,'created_at') else None
                print("-----------", create_date,"-----create_date------\n")
                modify_date = customer.updated_at if hasattr(customer,'updated_at') else None
                address = customer.addresses[0] if customer.addresses else None
                street = address.address1 if address and hasattr(address, 'address1') else ''
                street2 = address.address2 if address and hasattr(address, 'address2') else ''
                state_id = False
                if address and hasattr(address, 'province'):
                    state_name = address.province
                    state_record = self.env['res.country.state'].search([('name', '=', state_name)], limit=1)
                    state_id = state_record.id if state_record else False

                city = address.city if address and hasattr(address, 'city') else ''

                values = {
                    'shopify_customer_id':customer.id if hasattr(customer,'id') else '',
                    'name': f"{customer.first_name} {customer.last_name}" if hasattr(customer, 'first_name') or hasattr(
                        customer, 'last_name') else '',
                    'street': street,
                    'street2': street2,
                    'state_id': state_id,
                    'created_date':str_cre,
                    'modified_date':modify_date,
                    'city': city,
                    'email': customer.email if hasattr(customer, 'email') else '',
                    'phone': phone,
                    'from_shopify':True,
                }

                existing_customer = self.env['res.partner'].search([('shopify_customer_id', '=', values['shopify_customer_id'])], limit=1)

                if not existing_customer:
                    new_customer = self.env['res.partner'].create(values)
                    self.env.cr.commit()
                    print(f"Created new customer: {values['shopify_customer_id']} (ID: {new_customer.id})")

                else:
                    existing_customer.write(values)
                    print(f"Updated existing customer: {values['name']} (ID: {existing_customer.id})")


            if len(customers) < limit:
                print("Fetched all available customers.")
                get_next_page = False
            else:
                since_id = customers[-1].id

