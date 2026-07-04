from odoo import models, fields, api
import requests
import xmltodict
from datetime import date, datetime, timedelta, time


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wondersoft_customer=fields.Boolean(string='From wondersoft')
    wondersoft_id = fields.Char(string='Wondersoft customer')
    modified_date=fields.Date()
    created_date=fields.Date()

    def get_customer_wondersoft_creation(self):
        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/Token'
        access_token_header = {
            'SERVICE_METHODNAME': 'GetToken',
            'Username': 'WondersoftAPI',
            'Password': 'Wondersoft#1',
        }
        response = requests.post(url=access_token_url, headers=access_token_header)
        data_dict_access = xmltodict.parse(response.text)
        print("-----------", data_dict_access,"-----data_dict_access------\n")
        today_str = date.today().strftime("%Y/%m/%d")
        access_token=data_dict_access.get('Response', {}).get('Access_Token', None)
        print("-----------", access_token,"-----access_token------\n")
        wondersoft_customer_url='https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/ProcessData'
        all_records = []
        page_number = 1
        while True:
            wondersoft_customer_headers ={
                'SERVICE_METHODNAME': 'PullCustomer',
                'HEADER_FROMDATE':'2023-04-17',
                'HEADER_TODATE':'2024-10-19',
                # 'HEADER_STORECODE':'MylWH',
                'AUTHORIZATION': access_token,

            }
            product_response = requests.post(url=wondersoft_customer_url, headers=wondersoft_customer_headers)
            data_dict = xmltodict.parse(product_response.text)
            print("-----------", data_dict,"-----data_dict------\n")
            customers = data_dict.get('Response', {}).get('Customers', {}).get('Customer', [])
            if not customers:
                break
            all_records.extend(customers)
            print(f"Retrieved {len(customers)} products from page {page_number}.")
            for customer in customers:
                customer_code = customer.get('CustomerCode')
                customer_email = customer.get('CAEmail')
                customer_name = customer.get('CustomerName')
                customer_phone=customer.get('CAMobile')
                gstin = customer.get('GSTIN')

                address = customer.get('CAAddress1') if customer.get('CAAddress1') else None,
                address1 = customer.get('CAAddress2') if customer.get('CAAddress2') else None,
                city = customer.get('')
                customer_values=({
                    'name': customer_name,
                    'wondersoft_customer': True,
                    'email': customer_email,
                    'phone': customer_phone,
                    'street': address,
                    'street2': address1,
                    'wondersoft_id':customer_code,

                })
                print("-----------", customers,"-----customers------\n")
                existing_customer = self.env['res.partner'].search([('wondersoft_id', '=', customer_code)])
                if not existing_customer:
                    new_customer = self.env['res.partner'].create(customer_values)
                    self.env.cr.commit()
                    print(f"Created new customer: {customer_values['name']} (ID: {new_customer.id})")

                else:
                    existing_customer.write(customer_values)
                    print(f"Updated existing customer: {customer_values['name']} (ID: {existing_customer.id})")
            page_number += 1
        print(f"Total Customer retrieved: {len(all_records)}")

    def get_customer_wondersoft_update(self):
        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/Token'
        access_token_header = {
            'SERVICE_METHODNAME': 'GetToken',
            'Username': 'WondersoftAPI',
            'Password': 'Wondersoft#1',
        }
        response = requests.post(url=access_token_url, headers=access_token_header, verify=False)
        data_dict_access = xmltodict.parse(response.text)
        access_token = data_dict_access.get('Response', {}).get('Access_Token', None)
        print("-----------", access_token, "-----access_token------\n")
        wondersoft_customer_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/ProcessData'
        today_str_from = datetime.combine(datetime.today(), time.min).strftime("%Y-%m-%d %H:%M:%S")
        today_str_to = datetime.combine(datetime.today(), time.max).strftime("%Y-%m-%d %H:%M:%S")

        wondersoft_customer_headers = {
            'SERVICE_METHODNAME': 'PullCustomer',
            'AUTHORIZATION': access_token,
            'HEADER_FROMDATE':today_str_from,
            'HEADER_TODATE':today_str_to,
        }
        customer_update = requests.post(url=wondersoft_customer_url, headers=wondersoft_customer_headers)
        data_dict = xmltodict.parse(customer_update.text)
        print("-----------", data_dict,"-----data_dict------\n")
        customers = data_dict.get('Response', {}).get('Customers', {}).get('Customer', [])
        for customer in customers:
            customer_code = customer.get('CustomerCode')
            customer_email = customer.get('CAEmail')
            customer_name = customer.get('CustomerName')
            customer_phone = customer.get('CAMobile')
            gstin = customer.get('GSTIN')
            created_date = customer.get('CreatedDate')
            modified_date = customer.get('ModifiedDate')
            address = customer.get('CAAddress1') if customer.get('CAAddress1') else None,
            address1 = customer.get('CAAddress2') if customer.get('CAAddress2') else None,
            city = customer.get('')
            customer_values = ({
                'name': customer_name,
                'wondersoft_customer': True,
                'email': customer_email,
                'phone': customer_phone,
                'street': address,
                'street2': address1,
                'modified_date':modified_date,
                'created_date':created_date,

            })
            print("-----------", customers, "-----customers------\n")
            existing_customer = self.env['res.partner'].search([('phone', '=', customer_phone)])
            if not existing_customer:
                new_customer = self.env['res.partner'].create(customer_values)
                self.env.cr.commit()
                print(f"Created new customer: {customer_values['name']} (ID: {new_customer.id})")

            else:
                existing_customer.write(customer_values)
                print(f"Updated existing customer: {customer_values['name']} (ID: {existing_customer.id})")


