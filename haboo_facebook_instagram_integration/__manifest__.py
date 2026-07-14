{
    "name": "Facebook & Instagram Integration",
    "version": "19.0.1.0.0",
    "summary": """Capture leads and manage Facebook & Instagram social interactions from Odoo""",
    "description": """
        Facebook & Instagram Integration captures leads and manages
        Facebook and Instagram social-media interactions directly within
        Odoo CRM.
    """,
    "author": "Haboo Technologies Pvt Ltd",
    "website": "https://www.habootechnologies.com",
    "company": "Haboo Technologies Pvt Ltd",
    "maintainer": "Haboo Technologies Pvt Ltd",
    "license": "OPL-1",
    "price": 1,
    "support": "habootechnologies@gmail.com",
    "category": "Discuss",
    "depends": ['stock', 'crm', 'haboo_tata_whatsapp_integration'],
    "data": [
        "security/ir.model.access.csv",
        "views/platorm_views.xml",
        "views/views.xml",
        "views/crm_lead.xml",
        "wizard/opportunity_convert_wizard.xml",
        "views/res_partner_views_inherit.xml",
        "views/post_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            # JS/XML assets disabled pending OWL 2 rewrite (used Odoo 16 mail model API)
            # 'haboo_facebook_instagram_integration/static/src/js/reload_page.js',
            # 'haboo_facebook_instagram_integration/static/src/js/chatter.js',
            # 'haboo_facebook_instagram_integration/static/src/xml/chatter_message.xml',
        ],
    },
    "demo": [],
    "images": [
        "static/description/banner.png",
    ],
    "currency": "USD",
    "installable": True,
    "application": True,
    "auto_install": False,
}
