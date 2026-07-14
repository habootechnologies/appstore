# -*- coding: utf-8 -*-
{
    'name': "Qikberry Integration",
    'icon': 'static/description/icon.png',

    'summary': """
        Exchange business data and automate workflows between Odoo and
        Qikberry""",

    'description': """
        Qikberry Integration connects Odoo with the Qikberry platform
        to exchange business data and automate related workflows.
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
    'depends': ['base','crm'],

    'images': ['static/description/banner.png'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/group.xml',
        'views/qikberry_message.xml',
        'wizard/opport_convert.xml',
    ],
}
