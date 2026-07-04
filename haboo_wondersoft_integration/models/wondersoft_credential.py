from odoo import models, fields, api
import requests
import xmltodict


class WonderSoftCredential(models.Model):
    _name = 'wondersoft.credential'

    wondersoft_access_token = fields.Char()
    wondersoft_access_token_url = fields.Char()



    def get_access_token_from_wondersoft(self):
        access_token_var = ''
        access_token_url='https://eshopaiduat.giri.in/eshopaidrestservices/eShopaidService.svc/Token'
        access_token_header={
            'SERVICE_METHODNAME': 'GetToken',
            'Username': 'WondersoftAPI',
            'Password': 'Wondersoft#1',
        }
        response = requests.post(url=access_token_url, headers=access_token_header)

        data_dict = xmltodict.parse(response.text)
        access_token_var += data_dict.get('Response', {}).get('Access_Token', None)
        print("-----------", access_token_var,"-----access_token------\n")
        print(type(access_token_var))

        if access_token_var:
            record = self.browse(1)
            print("-----------", record,"-----product_record------\n")
            if record.exists():
                print("-----------", 1111,"-----1111------\n")
                record.write({'wondersoft_access_token': access_token_var})
                record.write({'wondersoft_access_token_url': access_token_url})
                print("-----------", self.wondersoft_access_token,"-----self.wondersoft_access_token------\n")
