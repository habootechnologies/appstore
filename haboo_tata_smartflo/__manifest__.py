# -*- coding: utf-8 -*-
{
    'name': "Haboo Tata SmartFlo Integration",
    'icon': 'static/description/icon.png',

    'summary': """
        Click-to-call, call logging, and telephony features in Odoo via
        Tata SmartFlo""",

    'description': """
        Haboo Tata SmartFlo Integration connects Odoo with Tata SmartFlo to
        enable click-to-call, call logging, and telephony features within
        Odoo CRM.
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
    'version': '19.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm'],

    'images': ['static/description/icon.png'],

    # always loaded
    'data': [
        'security/group.xml',
        'security/ir.model.access.csv',
        'views/crm_lead.xml',
        'views/cdr_history.xml',
        'views/res_config_settings.xml',
        'data/cron.xml',
        'wizard/opportunity_wizard.xml',
        # 'wizard/pop_up_wizard.xml',
    ],
}
