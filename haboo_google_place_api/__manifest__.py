{
    'name': 'Haboo Google Places & Reviews Integration',
    'summary': """Fetch and sync Google Business reviews and place details into Odoo""",
    'description': """
        Haboo Google Places & Reviews Integration connects Odoo with the
        Google Places API to automatically retrieve and populate business
        and location information, including Google Reviews, inside Odoo.
    """,
    'author': 'Haboo Technologies Pvt Ltd',
    'website': 'https://www.habootechnologies.com',
    'company': 'Haboo Technologies Pvt Ltd',
    'maintainer': 'Haboo Technologies Pvt Ltd',
    'license': 'OPL-1',
    'price': '1',
    'currency': 'USD',
    'support': 'habootechnologies@gmail.com',
    'category': 'Sales/CRM',
    'version': '19.0.1.0.0',
    'depends': ['base', 'base_setup', 'mail', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/sequence_data.xml',
        'views/google_reviews_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    'application': True,
    'images': ['static/description/banner.png'],
}
