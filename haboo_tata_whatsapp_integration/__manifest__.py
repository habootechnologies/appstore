# -*- coding: utf-8 -*-
{
    'name': "Haboo Tata WhatsApp Integration",

    'summary': """
        Send, receive, and manage Tata Tele Business WhatsApp conversations
        directly from Odoo, with support for two WhatsApp lines/numbers.""",

    'description': """
        Haboo Tata WhatsApp Integration connects Odoo CRM with the Tata Tele
        Business WhatsApp Cloud API, letting your team send and receive
        WhatsApp messages, auto-create/convert CRM opportunities from
        conversations, and track session SLAs from within Odoo. Supports a
        second independent WhatsApp line/number in parallel with the primary
        one.
    """,

    'author': "Haboo Technologies Pvt Ltd",
    'website': "https://www.habootechnologies.com",
    'company': "Haboo Technologies Pvt Ltd",
    'maintainer': "Haboo Technologies Pvt Ltd",

    'category': 'Sales/CRM',
    'version': '19.0.1.0.0',
    'license': 'OPL-1',
    'price': '1',
    'currency': 'USD',
    'support': 'habootechnologies@gmail.com',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'mail'],
    'assets': {
        'web.assets_backend': [
            # JS/XML assets disabled pending OWL 2 rewrite (used Odoo 16 mail model API)
            # 'haboo_tata_whatsapp_integration/static/src/js/reload_page.js',
            # 'haboo_tata_whatsapp_integration/static/src/js/chatter.js',
            # 'haboo_tata_whatsapp_integration/static/src/xml/chatter_message.xml',
            'haboo_tata_whatsapp_integration/static/src/css/custom.css',
        ],
    },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/group.xml',
        'security/group_2.xml',
        'data/tata_cron_data.xml',
        'data/tata_cron_data_2.xml',
        'views/views.xml',
        'views/views_2.xml',
        'views/crm_lead.xml',
        'views/crm_lead_2.xml',
        'views/whatup_user_session_view.xml',
        'views/whatup_user_session_view_2.xml',
        'wizard/opportunity_convert_wizard.xml',
        'wizard/opportunity_convert_wizard_2.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
