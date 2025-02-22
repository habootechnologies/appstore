from odoo import models, fields, api
import qrcode
import base64
from io import BytesIO
from odoo.exceptions import ValidationError


class ProductQrCode(models.Model):
    _name = 'product.qr.code'
    _description = 'Product QR Code'
    _rec_name = 'product_name'

    product_name = fields.Char("Product Name", readonly=True, default='New')
    product_id = fields.Many2one('product.template', 'Product')
    name = fields.Char(string="Name", compute='_compute_name', store=True)
    qr_code_image = fields.Binary(string='QR Code Image', attachment=False, readonly=True)
    file_name = fields.Char("Attachment Name", tracking=True, readonly=True)
    scanned = fields.Boolean(string='Scanned', default=False, readonly=True)
    scanned_on = fields.Datetime(string='Scanned On', readonly=True)
    scanned_by = fields.Many2one('res.users', string='Scanned By', readonly=True)
    id_record = fields.Char(string="ID" , readonly=True, default='New')
    id_product = fields.Char(string="Product ID")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('qr', 'QR'),
        ('in', 'In'),
        ('scanned', 'Scanned'),
        ('out', 'Out'),
    ], default='draft')
    in_date = fields.Date(string='In Date')
    out_date = fields.Date(string='Out Date')

    def action_qr(self):
        self.state = 'qr'

    def print_qr(self):
        self.ensure_one()
        if not self.qr_code_image:
            raise ValidationError("QR Code image not Generated")

        report = self.env.ref('haboo_qr_code.action_report_product_qr_code')

        return report.report_action(self, config=False)

    def action_add(self):
        self.state = 'in'
        self.in_date = fields.Date.today()

    def action_remove(self):
        self.state = 'out'
        self.out_date = fields.Date.today()





    @api.depends('name')
    def _compute_name(self):
        for record in self:
            if record.product_name:
               record.name = record.product_name
            else:
                record.name = "New"


    @api.model
    def create(self, vals):
        if not vals.get('product_name') or vals.get('product_name') == 'New':
            vals['product_name'] = self.env['ir.sequence'].next_by_code('product.qr.code.sequence')
            
        if not vals.get('id_record') or vals.get('id_record') == 'New':
            vals['id_record'] = self.env['ir.sequence'].next_by_code('product.qr.code')

        res = super(ProductQrCode, self).create(vals)
        if res.product_name:
            qr_image, filename = self._generate_qr(res.product_name, res.id)
            res.write({
                'qr_code_image': qr_image,
                'file_name': filename
            })
        return res


    def _generate_qr(self, product_name, record_id):
        code = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3, border=4)
        code.add_data(f"Product: {product_name},")
        code.add_data(f"Record_id: {record_id},")
        code.make(fit=True)
        img = code.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        filename = f"{product_name.replace(' ', '_')}.png"
        return qr_image, filename

    def mark_as_scanned(self):
        self.write({
            'scanned_on': fields.Datetime.now(),
            'scanned_by': self.env.user.id,
            'state': 'out',
        })
        self.out_date = fields.Date.today()


    


            

