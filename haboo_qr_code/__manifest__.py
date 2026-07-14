{
    'name': 'QR Code Generator and Scanner',
    'summary': """Generate and scan QR codes for Odoo products, with barcode-style scanning support""",
    'description': """
        QR Code Generator and Scanner for Odoo creates a unique QR code
        for every product and lets your team scan them directly from a
        browser camera or handheld scanner. Speed up inventory lookups,
        stock checks, and product identification with QR codes generated
        natively inside Odoo.
    """,
    'author': 'Haboo Technologies Pvt Ltd',
    'version': '16.0',
    'category': 'Inventory',
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
    'images': ['static/description/banner.png'],
    'application': True,

}