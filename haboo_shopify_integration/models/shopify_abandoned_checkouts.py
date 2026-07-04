from odoo import models, fields, api
import shopify
from datetime import datetime, timedelta,date,time

class AbandonedCheckouts(models.Model):
    _name = 'abandoned.checkouts'
    _description = 'Abandoned Checkouts'

    name = fields.Char(string='ID')
    shopify_customer = fields.Many2one('res.partner')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    date = fields.Datetime(string='Date')
    from_shopify = fields.Boolean()
    state = fields.Selection([('new','New'),('convert_to_opportunity','Convert to Opportunity')], default='new')
    abandoned_checkouts_lines_ids = fields.One2many('abandoned.checkout.order.line','abandoned_checkouts_id')
    company_currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id)
    price_subtotal = fields.Float(string="Subtotal", compute='compute_price_subtotal', store=True, currency_id='company_currency_id')
    is_boolean = fields.Boolean(default=True)
    country = fields.Char()
    country_code = fields.Char()
    oppur_converted = fields.Boolean(string="Converted to Opportunity", default=True)



    @api.depends('abandoned_checkouts_lines_ids', 'abandoned_checkouts_lines_ids.price_unit', 'abandoned_checkouts_lines_ids.quantity')
    def compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = sum([line.price_total for line in rec.abandoned_checkouts_lines_ids])



    def get_shopify_connection(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_api_key', False)
        access_token =self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_access_token', False)
        shop_name = self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_shop_name', False)
        version=self.env['ir.config_parameter'].sudo().get_param('haboo_shopify_integration.shopify_version', False)

        shop_url =f"https://{api_key}:{access_token}@{shop_name}.myshopify.com/admin/api/{version}"
        # shop_url = "https://<api_key>:<access_token>@<your-store>.myshopify.com/admin/api/2024-07"
        shopify.ShopifyResource.set_site(shop_url)
        print("Connected to Shopify API.")

    def _update_shopify_abandoned_checkouts_history_data(self, limit=100):
        self.get_shopify_connection()
        since_id = 0
        get_next_page = True
        current_date = fields.Datetime.now().date()
        today_date = date.today()
        today_str_from = datetime.combine(datetime.today(), time.min)
        today_str_to = datetime.combine(datetime.today(), time.max)
        today_str_from = (today_str_from - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        today_str_to = (today_str_to - timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        print("--------", today_str_to,"----today_str_to---\n")
        while get_next_page:
            abandoned_checkouts = shopify.Checkout.find(limit=limit,since_id=since_id,updated_at_min=f"{today_str_from}",updated_at_max=f"{today_str_to}",status="any")
            for checkout in abandoned_checkouts:
                print("--------", checkout,"----checkout---\n")
                cre_date = (datetime.strptime(checkout.created_at, '%Y-%m-%dT%H:%M:%S%z') - timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
                print("--------", checkout.customer.last_name,"----checkout.customer.last_name---\n")
                print("--------", type(checkout.customer.last_name) ,"----checkout.customer.last_name---\n")
                customer_name = checkout.customer.first_name
                customer_name = ""
                if checkout.customer:
                    if checkout.customer.first_name:
                        customer_name = checkout.customer.first_name
                    if checkout.customer.last_name:
                        customer_name += " " + checkout.customer.last_name if customer_name else checkout.customer.last_name
                customer = self.env['res.partner'].search([('shopify_customer_id', '=', checkout.customer.id)])
                if not customer:
                    customer = self.env['res.partner'].create({
                        'shopify_customer_id': checkout.customer.id,
                        'name': customer_name if customer_name else 'None',
                        'phone': checkout.customer.default_address.phone if hasattr(checkout.customer, "default_address") else "",

                    })
                existing_checkouts = self.env['abandoned.checkouts'].search([('name', '=', checkout.id)])
                if not existing_checkouts:
                    line_values = []
                    phone = ''
                    if checkout.customer.phone:
                        phone += checkout.customer.phone
                    elif hasattr(checkout.customer, 'default_address') and checkout.customer.default_address.phone:
                        phone += checkout.customer.default_address.phone

                    elif hasattr(checkout.customer, 'shipping_address') and checkout.customer.shipping_address.phone:
                        phone += checkout.customer.shipping_address.phone
                    elif hasattr(checkout.customer, 'billing_address') and checkout.customer.billing_address.phone:
                        phone += checkout.customer.billing_address.phone
                    new_checkout = self.env['abandoned.checkouts'].create({
                        'name': checkout.id,
                        'date': cre_date,
                        'phone': phone or " ",
                        'email': checkout.customer.email,
                        'country_code': checkout.shipping_address.country if checkout.customer and hasattr(checkout, "shipping_address") and checkout.shipping_address else "unknown",
                        'country':checkout.customer.default_address.country_name if checkout.customer and hasattr(checkout.customer, "default_address") and checkout.customer.default_address else "unknown",
                        'shopify_customer': customer.id if customer else False,
                    })
                    print("--------", line_values,"----line_values---\n")
                    for line in checkout.line_items:
                        product_id = self.env['product.template'].search([('product_id', '=', line.product_id)], limit=1)
                        if not product_id:
                            product_id = self.env['product.template'].create({'name': line.title,'product_id': line.product_id, 'default_code': line.sku})
                        taxes = False
                        # if line.tax_lines:
                        #     print("--------", line.tax_lines[0].title + ' ' + str(int(line.tax_lines[0].rate*100)) + '%',"----line.tax_lines[0].title + ' ' + str(int(line.tax_lines[0].rate*100)) + '%'---\n")
                        #     taxes = self.env['account.tax'].search([('name', '=', line.tax_lines[0].title + ' ' + str(line.tax_lines[0].rate*100) + '%')])
                        line_values.append((0, 0, {'shopify_product_template_id': product_id.id, 'name': line.presentment_title, 'quantity': line.quantity, 'price_unit': line.price, 'price_total': line.line_price}))
                    shipping_product = self.env['product.template'].search([('is_shipping_product', '=', True)], limit=1)
                    if checkout.shipping_lines and shipping_product:
                        line_values.append((0, 0, {'shopify_product_template_id': shipping_product.id, 'name': checkout.shipping_lines[0].title, 'quantity': 1, 'price_unit': checkout.shipping_lines[0].price, 'price_total': checkout.shipping_lines[0].price}))
                    new_checkout.abandoned_checkouts_lines_ids = line_values
                    self.env.cr.commit()
            if len(abandoned_checkouts) < limit:
                get_next_page = False
                print("Fetched all available orders.")
            else:
                since_id = abandoned_checkouts[-1].id
                print("--------", since_id, "----since_id---\n")


    def create_opportunity_wizard(self):
        self.write({'is_boolean': False})
        self.write({'state':'convert_to_opportunity'})
        # partner = self.env['res.partner'].search([('phone', '=', self.client_number)], limit=1)
        partner = self.env['res.partner'].browse(self.shopify_customer.id)
        print("-----------", partner,"-----partner------\n")
        # existing_opportunities = self.env['crm.lead'].search([('phone', '=', self.client_number)])
        domain = []
        if self.name:
            domain.append(('partner_id', '=', self.shopify_customer.id))
        else:
            domain.append(('id', 'in', []))
        existing_opportunities = self.env['crm.lead'].search(domain)
        self.oppur_converted = False
        print("-----------", existing_opportunities,"-----existing_opportunities------\n")
        return {
            'name': 'Convert to Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'shopify.opportunity.convert.wizard',
            'view_mode': 'form',
            'context': {
                'default_shopify_history_ids': [(6, 0, self.id)],
                'default_conversion_action': 'merge' if existing_opportunities else 'convert',
                'default_user_id': self.env.user.id,
                'default_partner_action': 'exist' if partner else 'create',
                'default_partner_id': partner.id if partner else False,
                'default_phone': self.phone if self.phone else "+91-XXXXXXXXXX",
                'default_email':self.email if self.email else "default123@gmail.com",
                'default_partner_name':self.shopify_customer.name,
                'default_shopify_id': self.id,
                'default_opportunity_ids': existing_opportunities.ids if existing_opportunities else False,
            },
            'target': 'new',
        }

    def action_view_opportunity(self):
        return {
            'name': 'Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'list,form',
            'domain': [('shopify_history_ids', 'in', self.id)],
        }







class AbandonedCheckoutOrderLine(models.Model):
    _name='abandoned.checkout.order.line'

    abandoned_checkouts_id= fields.Many2one('abandoned.checkouts')
    shopify_product_template_id = fields.Many2one('product.template')
    name = fields.Text(string='Description')
    sku_code = fields.Char(related='shopify_product_template_id.default_code')
    currency_id = fields.Many2one('res.currency', 'Currency')
    price_unit = fields.Float(string='Unit Price')
    quantity = fields.Integer(string='Quantity')
    product_uom_id = fields.Many2one('uom.uom')
    tax_ids = fields.Many2many('account.tax')
    price_total = fields.Monetary(string="Total")
    price_subtotal = fields.Monetary(string="Subtotal")





