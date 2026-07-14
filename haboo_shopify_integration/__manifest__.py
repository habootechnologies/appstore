{
    'name': "Shopify Integration",

    'summary': """
        Synchronize products, customers, orders, inventory, and fulfillment
        between Shopify and Odoo""",

    'description': """
        Shopify Integration synchronizes products, customers, orders,
        inventory, and fulfillment information between Shopify and Odoo,
        including abandoned checkout recovery via CRM.
    """,

    'author': "Haboo Technologies Pvt Ltd",
    'website': "https://www.habootechnologies.com",
    'company': "Haboo Technologies Pvt Ltd",
    'maintainer': "Haboo Technologies Pvt Ltd",
    'license': 'OPL-1',
    'price': '1',
    'currency': 'USD',
    'support': 'habootechnologies@gmail.com',

    'category': 'Sales/CRM',
    'version': '16.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm','sale', 'product','web'],

    # always loaded

    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/shopify_product_conf.xml',
        'views/res_config_settings.xml',
        'views/shopify_customer_conf.xml',
        # 'views/shopify_dashboard.xml',
        'views/crm_lead_shopify.xml',
        'views/shopify_order_conf.xml',
        'views/shopify_adandoned_checkouts.xml',
        'wizard/opportunity_wizard.xml',

    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'haboo_shopify_integration/static/src/scss/shopify_graph_widget.scss',
    #         'haboo_shopify_integration/static/src/js/shopify_crm_dashboard.js',
    #         'haboo_shopify_integration/static/src/xml/shopify_crm_dasboard.xml',
    #     ],
    # },
    'images': ['static/description/banner.png'],
}
