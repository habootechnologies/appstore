# -*- coding: utf-8 -*-
{
    'name': "Haboo Qikberry Integration",
    'icon': 'static/description/logo.png',

    'summary': """
        Exchange business data and automate workflows between Odoo and
        Qikberry""",

    'description': """
        Haboo Qikberry Integration connects Odoo with the Qikberry platform
        to exchange business data and automate related workflows.
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
    'depends': ['base','crm'],

    'images': ['static/description/logo.png'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/group.xml',
        'views/qikberry_message.xml',
        'wizard/opport_convert.xml',
    ],
}
