# -*- coding: utf-8 -*-
{
    'name': "Lime Chat Integration",

    'summary': """
        Manage LimeChat chatbot and customer support conversations from
        Odoo CRM""",

    'description': """
        Lime Chat Integration connects Odoo with LimeChat, syncing
        chatbot and customer support conversations into Odoo CRM. Convert
        any LimeChat conversation into a CRM opportunity in one click,
        with full conversation history and role-based access control.
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
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm'],

    # always loaded
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv',
        'wizard/lime_chat_convert_opportunity_views.xml',
        'views/haboo_lime_chat.xml',

    ],
    'images': ['static/description/banner.png'],
}
