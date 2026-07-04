{
    "name": "Haboo Facebook & Instagram Messenger Integration",
    "version": "19.0.1.0.0",
    "summary": """Bidirectional Facebook Messenger and Instagram Messaging integration
        for Odoo, built on the Facebook/Instagram Graph API by Meta""",
    "description": """
        Haboo Facebook & Instagram Messenger Integration connects Odoo Discuss
        with the Facebook/Instagram Graph API by Meta, allowing users to send
        and receive Facebook Messenger and Instagram DMs directly from Odoo,
        with full conversation history against contacts and leads.
    """,
    "category": "Discuss",
    "author": "Haboo Technologies Pvt Ltd",
    "website": "https://www.habootechnologies.com",
    "company": "Haboo Technologies Pvt Ltd",
    "maintainer": "Haboo Technologies Pvt Ltd",
    "license": "OPL-1",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/messenger_compose_message_view.xml",
        "wizard/instagram_compose_message_view.xml",
        "views/mail_channel.xml",
        "views/messenger_provider_base.xml",
        "views/messenger_history_views.xml",
        "views/mail_message_views.xml",
        "views/instagram_history_views.xml",
        "views/messenger_channel_provider_line_views.xml",
        "views/res_partner_views_inherit.xml",
        "views/res_users_inherit.xml",
        "views/messenger_template_views.xml",
        "views/template_buttons_views.xml",
        "views/template_components_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # JS assets disabled pending OWL 2 rewrite
            # (used Odoo 16 registerMessagingComponent/registerPatch API removed in Odoo 17+)
            # "haboo_facebook_instagram_messenger/static/src/js/chat_view_nav.js",
            # "haboo_facebook_instagram_messenger/static/src/js/thread_view_nav.js",
            # "haboo_facebook_instagram_messenger/static/src/js/thread.js",
            # "haboo_facebook_instagram_messenger/static/src/xml/*.xml",
            "haboo_facebook_instagram_messenger/static/src/scss/*.scss",
        ],
    },
    "demo": [],
    "images": [
        "static/description/banner.png",
    ],
    "price": 1,
    "currency": "USD",
    "support": "habootechnologies@gmail.com",
    "installable": True,
    "application": True,
    "auto_install": False,
}
