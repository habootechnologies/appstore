from odoo import models, fields, api


class ProductTemplate(models.Model):
   _inherit = 'product.template'

   # def get_products(self):
   #    shop_products = {}
   #    total_count = 0
   #
   #    self._cr.execute(
   #       """select count(id) as total_count from product_template where shopify_instance_id = %s""" % self.id)
   #    result = self._cr.dictfetchall()
   #
   #    if result:
   #       total_count = result[0].get('total_count')
   #
   #    view = self.env.ref('sale.product_template_action').read()[0]
   #    action = self.create_action(view, [('shopify_instance_id', '=', self.id)])
   #    action.update({
   #       'context': "{'shopify_instance_id': " + str(self.id) + ", 'search_default_shopify_imported_products': 1}",
   #    })
   #    shop_products.update({
   #       'product_count': total_count,
   #       'product_action': action
   #    })
   #
   #    return shop_products

