from odoo import models, fields, api
import requests
import xmltodict
from datetime import date, datetime, timedelta,time



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    access_product = fields.Char()
    wondersoft_product = fields.Boolean()

   

    def get_product_from_wondersoft(self):
        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/Token'
        access_token_header = {
            'SERVICE_METHODNAME': 'GetToken',
            'Username': 'WondersoftAPI',
            'Password': 'Wondersoft#1',
        }

        response = requests.post(url=access_token_url, headers=access_token_header)
        data_dict_access = xmltodict.parse(response.text)
        access_token = data_dict_access.get('Response', {}).get('Access_Token', None)

        if not access_token:
            print("Failed to retrieve access token.")
            return

        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/ProcessData'
        all_records = []
        page_number = 1
        while True:

            access_token_header = {
                'SERVICE_METHODNAME': 'GetProducts',
                'AUTHORIZATION': access_token,
                'HEADER_PAGENO': str(page_number),
                'HEADER_FROMDATE': '2024-10-17',
                'HEADER_TODATE': '2024-10-17',

            }
            params = {
                "DateFilter": '',
            }
            response = requests.post(url=access_token_url, headers=access_token_header, params=params)
            data_dict = xmltodict.parse(response.text)
            products = data_dict.get('Response', {}).get('Data', {}).get('Product', [])

            print("-----------", type(products),"-----products------\n")
            if not products:
                break
            all_records.extend(products)
            print(f"Retrieved {len(products)} products from page {page_number}.")

            for product in products:
                print("-----------", type(product),"-----product------\n")
                product_code = product.get('ProductCode')
                print("-----------", product_code,"-----product_code------\n")
                product_name = product.get('ProductName')
                sales_price = float(product.get('SalesPrice', 0.0))
                product_value = ({
                    'name': product_name,
                    'default_code': product_code,
                    'list_price': sales_price,
                    'wondersoft_product': True,

                })

                existing_product = self.search([('default_code', '=', product_code)], limit=1)
                if not existing_product:
                    new_product = self.env['product.template'].create(product_value)
                    print(f"Created new product: {product_value['name']} (ID: {new_product.id})")
                    self.env.cr.commit()

                else:
                    existing_product.write(product_value)
                    print(f"Updated existing product: {product_value['name']} (ID: {existing_product.id})")

            page_number += 1

        print(f"Total products retrieved: {len(all_records)}")


    def get_product_from_wondersoft_update(self):
        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/Token'
        access_token_header = {
            'SERVICE_METHODNAME': 'GetToken',
            'Username': 'WondersoftAPI',
            'Password': 'Wondersoft#1',
        }

        response = requests.post(url=access_token_url, headers=access_token_header)
        data_dict_access = xmltodict.parse(response.text)
        access_token = data_dict_access.get('Response', {}).get('Access_Token', None)

        if not access_token:
            print("Failed to retrieve access token.")
            return

        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/ProcessData'
        all_records = []
        page_number = 1
        while True:

            access_token_header = {
                'SERVICE_METHODNAME': 'GetProducts',
                'AUTHORIZATION': access_token,
                'HEADER_PAGENO': str(page_number),
            }
            params = {
                "DateFilter": '',
            }
            response = requests.post(url=access_token_url, headers=access_token_header, params=params)
            data_dict = xmltodict.parse(response.text)
            print("-----------", data_dict,"-----data_dict------\n")
            products = data_dict.get('Response', {}).get('Data', {}).get('Product', [])
            print("-----------", type(products),"-----products------\n")

            if not products:
                break
            all_records.extend(products)
            print(f"Retrieved {len(products)} products from page {page_number}.")
            for product in products:
                print("-----------", type(product),"-----type(product)------\n")
                product_code = product.get('ProductCode')
                product_name = product.get('ProductName')
                sales_price = float(product.get('SalesPrice', 0.0))
                created_date_str = product.get('CreatedOn')
                modified_date_str = product.get('ModifiedOn')
                product_value = ({
                    'name': product_name,
                    'default_code': product_code,
                    'list_price': sales_price,
                    'wondersoft_product': True,

                })
                created_date = datetime.strptime(created_date_str, '%Y-%m-%d %H:%M:%S').date()
                print("Created Date:", created_date)
                modified_date = datetime.strptime(modified_date_str, '%Y-%m-%d %H:%M:%S').date()
                print("Modified Date:", modified_date)


                # if modified_date_str:
                #     modified_date = datetime.strptime(modified_date_str, '%Y-%m-%d %H:%M:%S').date()
                #     print("Modified Date:", modified_date)
                # else:
                #     print("Modified date not available.")
                today_str = datetime.now().date()
                existing_product = self.search([('default_code', '=', product_code)], limit=1)
                if created_date_str == str(today_str):
                    new_product = self.env['product.template'].create(product_value)
                    print(f"Created new product: {product_value['name']} (ID: {new_product.id})")
                    self.env.cr.commit()
                elif modified_date_str >= str(today_str):
                    existing_product.write(product_value)
                    print(f"Updated existing product: {product_value['name']} (ID: {existing_product.id})")
                else:
                    print("-----------", "Date not found","-----Date not found------\n")
                





