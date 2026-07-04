# -*- coding: utf-8 -*-
{
    'name': "Haboo Gupshup WhatsApp Integration",

    'summary': """
        Send, receive, and manage WhatsApp messages from Odoo via the
        Gupshup WhatsApp Business API""",

    'description': """
        Haboo Gupshup WhatsApp Integration connects Odoo with the Gupshup
        WhatsApp Business API, letting your team send, receive, and manage
        WhatsApp conversations directly from Odoo.
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
