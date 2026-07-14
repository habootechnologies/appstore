{
    'name': 'Google Places & Reviews Integration',
    'summary': """Sync Google Business Reviews and Place details into Odoo CRM""",
    'description': """
        Google Places & Reviews Integration connects Odoo to the Google
        Places API, automatically fetching and syncing Google Reviews and
        business location details into Odoo CRM. Track ratings, reviewer
        feedback, and place information without leaving Odoo or checking
        Google Business Profile separately.
    """,
    'author': 'Technologies Pvt Ltd',
    'website': 'https://www.habootechnologies.com',
    'company': 'Technologies Pvt Ltd',
    'maintainer': 'Technologies Pvt Ltd',
    'license': 'OPL-1',
    'price': '1',
    'currency': 'USD',
    'support': 'habootechnologies@gmail.com',
    'category': 'Sales/CRM',
    'version': '17.0.1.0.0',
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
