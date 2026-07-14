# -*- coding: utf-8 -*-
{
    'name': "Lime Chat Integration",

    'summary': """
        Manage LimeChat chatbot conversations and customer support
        interactions from Odoo""",

    'description': """
        Lime Chat Integration connects Odoo with LimeChat to manage
        chatbot conversations and customer support interactions directly
        from Odoo CRM.
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
    'version': '18.0.1.0.0',

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
