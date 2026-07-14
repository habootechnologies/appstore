{
    'name': "Wondersoft Integration",

    'summary': """
        Sync products, customers, inventory and transactions between
        Odoo and Wondersoft ERP/POS""",

    'description': """
        Wondersoft Integration synchronizes products, customers,
        inventory, and transaction data between Odoo and the Wondersoft
        ERP/POS system on a scheduled basis, keeping both systems
        aligned without manual data entry.
    """,

    'author': "Technologies Pvt Ltd",
    'website': "https://www.habootechnologies.com",
    'company': "Technologies Pvt Ltd",
    'maintainer': "Technologies Pvt Ltd",
    'license': 'OPL-1',
    'price': '1',
    'currency': 'USD',
    'support': 'habootechnologies@gmail.com',

    'category': 'Sales/CRM',
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale', 'haboo_shopify_integration'],

    'icon': 'static/description/icon.png',
    'images': ['static/description/banner.png'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/wondersoft_credential.xml',
        'views/crm_lead.xml',
        'views/wondersoft_products.xml',
        'views/wondersoft_customers.xml',
        'views/wondersoft_order.xml',
    ],
}
