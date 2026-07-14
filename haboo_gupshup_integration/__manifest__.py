# -*- coding: utf-8 -*-
{
    'name': "Gupshup WhatsApp Integration",

    'summary': """
        Send and receive WhatsApp messages in Odoo via the Gupshup
        WhatsApp Business API""",

    'description': """
        Gupshup WhatsApp Integration connects Odoo with the Gupshup
        WhatsApp Business API, letting your team send, receive, and manage
        WhatsApp Business conversations directly from Odoo CRM. Full
        message history, a built-in reply wizard, and CRM lead linkage for
        every WhatsApp conversation.
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
    'version': '17.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/gupshup_message_history.xml',
        'views/res_config_settings.xml',
        'wizard/send_reply_wizard.xml',
    ],
    'images': ['static/description/banner.png'],
}
