# -*- coding: utf-8 -*-
{
    'name': "Tata SmartFlo Integration",
    'icon': 'static/description/icon.png',

    'summary': """
        Click-to-call, call logging, and telephony features in Odoo via
        Tata SmartFlo""",

    'description': """
        Tata SmartFlo Integration connects Odoo with Tata SmartFlo to
        enable click-to-call, call logging, and telephony features within
        Odoo CRM.
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
    'version': '15.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm'],

    'images': ['static/description/banner.png'],

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
