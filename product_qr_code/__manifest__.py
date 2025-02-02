{
    'name': 'QR Code Generator and Scanner',
    'summary': """QR Code Generator and Scanner""",
    'description': """QR Code Generator and Scanner""",
    'version': '17.0',
    'category': 'Inventory',
    'summary': 'Generate and Scan QR codes for Products',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/product_qr_code_views.xml',
        'reports/report_qr_code.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'product_qr_code/static/src/js/product_qr_code_scan.js',
            'product_qr_code/static/src/js/html5-qrcode.js',
            'product_qr_code/static/src/xml/product_qr_code_template.xml',
        ],
    },
    'installable': True,
    'license': 'OPL-1',
    'price': '1',
    'currency': 'USD',
    'support': 'habootechnologies@gmail.com',
    'images': ['static/description/b1.png'],
    'application': True,

}