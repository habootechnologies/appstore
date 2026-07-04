from odoo import models, fields, api
import requests
import xmltodict
from datetime import date, datetime, timedelta,time



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    wondersoft_order = fields.Char()
    from_wondersoft = fields.Boolean()
    store_code = fields.Char()


    def get_wondersoft_sale_order_creation(self):
        access_token_url = 'https://giri.eshopaid.com/eshopaid_CRM_restservices/eshopaidservice.svc/Token'
        access_token_header = {
            'SERVICE_METHODNAME': 'GetToken',
            'Username': 'WondersoftCRM',
            'Password': 'Wondersoft#2',
        }
        response = requests.post(url=access_token_url, headers=access_token_header)
        data_dict_access = xmltodict.parse(response.text)
        access_token = data_dict_access.get('Response', {}).get('Access_Token', None)
        # today_str_from = datetime.combine(datetime.today(), time.min)
        # today_str_to = datetime.combine(datetime.today(), time.max)
        # today_str_from = (today_str_from - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        # today_str_to = (today_str_to - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        today_str_from = datetime.today().strftime("%Y-%m-%d")
        today_str_to = datetime.today().strftime("%Y-%m-%d")
        access_token_url = 'https://giri.eshopaid.com/eshopaid_CRM_restservices/eshopaidservice.svc/ProcessData'
        access_token_header = {
            'SERVICE_METHODNAME': 'PullSales',
            'AUTHORIZATION': access_token,
            'HEADER_FROMDATE':today_str_from,
            'HEADER_TODATE': today_str_to,
            'HEADER_MODE': 'Sales',
            'HEADER_B2BFLAG': '1',
            'HEADER_STORECODE': '',
            'HEADER_PAGENO': '',
        }
        response = requests.post(url=access_token_url, headers=access_token_header)
        data_dict = xmltodict.parse(response.text)
        pages = data_dict.get('Response', {}).get('WsTransaction', {}).get('PageSummary', {}).get('PageCount')
        sale_count = 0
        for i in range(1, int(pages) + 1):
            print("--------", i,"----i---\n")

            access_token_url = 'https://giri.eshopaid.com/eshopaid_CRM_restservices/eshopaidservice.svc/ProcessData'
            access_token_header = {
                'SERVICE_METHODNAME': 'PullSales',
                'AUTHORIZATION': access_token,
                'HEADER_FROMDATE': today_str_from,
                'HEADER_TODATE': today_str_to,
                'HEADER_MODE': 'Sales',
                'HEADER_B2BFLAG': '1',
                'HEADER_STORECODE': '',
                'HEADER_PAGENO': str(i),
            }
            response = requests.post(url=access_token_url, headers=access_token_header)
            data_dict = xmltodict.parse(response.text)
            sales_data = data_dict.get('Response', {}).get('WsTransaction', {}).get('Sales', [])
            sale_count += len(sales_data)

            for order in sales_data:
                order_no = order.get('CustomerCode')
                doc_no = order.get('DocNumber')
                customer_name = order.get('CustomerName') or "Default Name"
                date = order.get('BillDate')
                store_code = order.get('StoreName')
                customer_street1 = order.get('DeliveryAddress1') or "Default Address"
                customer_street2 = order.get('DeliveryAddress2') or ""
                customer_street3 = order.get('DeliveryAddress3') or ""
                customer_state = order.get('DeliveryStateName') or "Default State"
                customer_city = order.get('DeliveryCityCode') or "Default City"
                customer_zip = order.get('DeliveryPinCode') or "000000"
                customer_phone = order.get('CustomerMobile') or "0000000000"
                customer_email = order.get('CustomerEmail') or "default@example.com"

                state_id = False
                if customer_state != "Default State":
                    state_record = self.env['res.country.state'].search([('name', '=', customer_state)], limit=1)
                    state_id = state_record.id if state_record else False

                customer = self.env['res.partner'].search([('phone', '=', customer_phone)], limit=1)
                if customer:
                    customer.write({
                        'street': customer_street1,
                        'street2': customer_street2,
                        'state_id': state_id,
                        'city': customer_city,
                        'zip': customer_zip,
                        'email': customer_email,
                        'phone': customer_phone,
                    })
                else:
                    customer = self.env['res.partner'].create({
                        'name': customer_name,
                        'street': customer_street1,
                        'street2': customer_street2,
                        'state_id': state_id,
                        'city': customer_city,
                        'zip': customer_zip,
                        'email': customer_email,
                        'phone': customer_phone,
                    })

                sale_order = self.env['sale.order'].search([
                    ('partner_id', '=', customer.id),
                    ('name', '=', doc_no),
                ], limit=1)

                items = order.get('Items', {}).get('Item', [])
                if isinstance(items, dict):
                    items = [items]

                if sale_order:
                    sale_order.write({
                        'date_order': date,
                        'from_wondersoft': True,
                        'store_code': store_code,
                    })
                    
                    # sale_order.order_line.unlink()
                    existing_lines = {line.product_id.default_code: line for line in sale_order.order_line}
                    for item in items:
                        product_code = item.get('ProductCode')
                        quantity = float(item.get('Quantity', 0))
                        sales_price = float(item.get('SalesPrice', 0))
                        base_value = float(item.get('BaseValue', 0))
                        tax_percentage = float(item.get('EffectiveTaxPercentage', 0))
                        product_name = item.get('ProductName', 'Unnamed Product')

                        product = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                        if not product:
                            product = self.env['product.product'].create({
                                'name': product_name,
                                'default_code': product_code,
                                'list_price': sales_price,
                                'wondersoft_product':True,
                            })

                        tax = self.env['account.tax'].search([('amount', '=', tax_percentage)], limit=1)
                        if not tax:
                            tax = self.env['account.tax'].create({
                                'name': f'{tax_percentage}% GST',
                                'amount': tax_percentage,
                                'amount_type': 'percent',
                                'type_tax_use': 'sale',
                            })

                        if product_code in existing_lines:
                            # Update existing order line
                            existing_line = existing_lines[product_code]
                            existing_line.write({
                                'product_uom_qty': quantity,
                                'price_unit': base_value,
                                'tax_id': [(6, 0, [tax.id])],
                                'price_subtotal': sales_price,
                            })
                

                else:
                    sale_order = self.env['sale.order'].create({
                        'wondersoft_order': order_no,
                        'name': doc_no,
                        'partner_id': customer.id,
                        'currency_id': self.env.user.company_id.currency_id.id,
                        'date_order': date,
                        'partner_invoice_id': customer.id,
                        'partner_shipping_id': customer.id,
                        'pricelist_id': self.env['product.pricelist'].search([], limit=1).id,
                        'warehouse_id': self.env['stock.warehouse'].search([], limit=1).id,
                        'company_id': self.env.user.company_id.id,
                        'from_wondersoft': True,
                        'store_code': store_code,
                    })
                    print('########## sale_order ###############', sale_order)

                    for item in items:
                        product_code = item.get('ProductCode')
                        quantity = float(item.get('Quantity', 0))
                        sales_price = float(item.get('SalesPrice', 0))
                        tax_amount = float(item.get('TaxAmount', 0))
                        base_value = float(item.get('BaseValue', 0))
                        tax_percentage = float(item.get('EffectiveTaxPercentage', 0))
                        product_name = item.get('ProductName', 'Unnamed Product')

                        product = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                        if not product:
                            product = self.env['product.product'].create({
                                'name': product_name,
                                'default_code': product_code,
                                'list_price': sales_price,
                                'wondersoft_product': True,

                            })

                        tax = self.env['account.tax'].search([('amount', '=', tax_percentage)], limit=1)
                        if not tax:
                            tax = self.env['account.tax'].create({
                                'name': f'{tax_percentage}% GST',
                                'amount': tax_percentage,
                                'amount_type': 'percent',
                                'type_tax_use': 'sale',
                            })

                        self.env['sale.order.line'].create({
                            'order_id': sale_order.id,
                            'product_id': product.id,
                            'product_uom_qty': quantity,
                            'price_unit': base_value,
                            'name': product_name,
                            'tax_id': [(6, 0, [tax.id])],
                            'price_subtotal': sales_price,
                        })

                self.env.cr.commit()

    def get_wondersoft_sale_order_creation_one(self):
        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/Token'
        access_token_header = {
            'SERVICE_METHODNAME': 'GetToken',
            'Username': 'WondersoftAPI',
            'Password': 'Wondersoft#1',
        }
        response = requests.post(url=access_token_url, headers=access_token_header)
        print("-----------", response, "-----response------\n")
        data_dict_access = xmltodict.parse(response.text)
        access_token = data_dict_access.get('Response', {}).get('Access_Token', None)
        print("-----------", access_token, "-----access_token------\n")
        access_token_url = 'https://eshopaid.giri.in/eshopaid_CRM_restservices/eShopaidService.svc/ProcessData'
        access_token_header = {
            'SERVICE_METHODNAME': 'PullSales',
            'AUTHORIZATION': access_token,
            # 'HEADER_FROMDATE': '2023-12-28',
            # 'HEADER_TODATE': '2023-12-28',
            'HEADER_MODE': 'Sales',
            'HEADER_B2BFLAG': '1',
            'HEADER_STORECODE': '',
            'HEADER_PAGENO': '1',
        }
        response = requests.post(url=access_token_url, headers=access_token_header)
        data_dict = xmltodict.parse(response.text)
        sales_data = data_dict.get('Response', {}).get('WsTransaction', {}).get('Sales', [])
        # sale_count += len(sales_data)

        for order in sales_data:
            print("-----------", order, "-----order------\n")
            order_no = order.get('CustomerCode')
            doc_no = order.get('DocNumber')
            store_code = order.get('StoreName')
            customer_name = order.get('CustomerName') or "Default Name"
            date = order.get('CreatedOn')
            customer_street1 = order.get('DeliveryAddress1') or "Default Address"
            customer_street2 = order.get('DeliveryAddress2') or ""
            customer_street3 = order.get('DeliveryAddress3') or ""
            customer_state = order.get('DeliveryStateName') or "Default State"
            customer_city = order.get('DeliveryCityCode') or "Default City"
            customer_zip = order.get('DeliveryPinCode') or "000000"
            customer_phone = order.get('CustomerMobile') or "0000000000"
            customer_email = order.get('CustomerEmail') or "default@example.com"

            state_id = False
            if customer_state != "Default State":
                state_record = self.env['res.country.state'].search([('name', '=', customer_state)], limit=1)
                state_id = state_record.id if state_record else False

            customer = self.env['res.partner'].search([('name', '=', customer_name)], limit=1)
            if customer:
                customer.write({
                    'street': customer_street1,
                    'street2': customer_street2,
                    'state_id': state_id,
                    'city': customer_city,
                    'zip': customer_zip,
                    'email': customer_email,
                    'phone': customer_phone,
                })
            else:
                customer = self.env['res.partner'].create({
                    'name': customer_name,
                    'street': customer_street1,
                    'street2': customer_street2,
                    'state_id': state_id,
                    'city': customer_city,
                    'zip': customer_zip,
                    'email': customer_email,
                    'phone': customer_phone,
                })

            sale_order = self.env['sale.order'].search([
                ('partner_id', '=', customer.id),
                ('wondersoft_order', '=', order_no)
            ], limit=1)

            items = order.get('Items', {}).get('Item', [])
            if isinstance(items, dict):
                items = [items]

            if sale_order:
                sale_order.write({
                    'date_order': date,
                    'from_wondersoft': True,
                    'store_code': store_code,

                })
                # sale_order.order_line.unlink()


            else:
                sale_order = self.env['sale.order'].create({
                    'wondersoft_order': order_no,
                    'name': doc_no,
                    'partner_id': customer.id,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'date_order': date,
                    'partner_invoice_id': customer.id,
                    'partner_shipping_id': customer.id,
                    'pricelist_id': self.env['product.pricelist'].search([], limit=1).id,
                    'warehouse_id': self.env['stock.warehouse'].search([], limit=1).id,
                    'company_id': self.env.user.company_id.id,
                    'from_wondersoft': True,
                    'store_code': store_code,
                })

                for item in items:
                    print("-----------", item, "-----item------\n")
                    product_code = item.get('ProductCode')
                    quantity = float(item.get('Quantity', 0))
                    sales_price = float(item.get('SalesPrice', 0))
                    tax_amount = float(item.get('TaxAmount', 0))
                    base_value = float(item.get('BaseValue', 0))
                    tax_percentage = float(item.get('EffectiveTaxPercentage', 0))
                    product_name = item.get('ProductName', 'Unnamed Product')

                    product = self.env['product.product'].search([('default_code', '=', product_code)], limit=1)
                    if not product:
                        product = self.env['product.product'].create({
                            'name': product_name,
                            'default_code': product_code,
                            'list_price': sales_price,
                        })

                    tax = self.env['account.tax'].search([('amount', '=', tax_percentage)], limit=1)
                    if not tax:
                        tax = self.env['account.tax'].create({
                            'name': f'{tax_percentage}% GST',
                            'amount': tax_percentage,
                            'amount_type': 'percent',
                            'type_tax_use': 'sale',
                        })

                    self.env['sale.order.line'].create({
                        'order_id': sale_order.id,
                        'product_id': product.id,
                        'product_uom_qty': quantity,
                        'price_unit': base_value,
                        'name': product_name,
                        'tax_id': [(6, 0, [tax.id])],
                        'price_subtotal': sales_price,
                    })

            self.env.cr.commit()
            print("-----------", sale_order, "-----sale_order------\n")
