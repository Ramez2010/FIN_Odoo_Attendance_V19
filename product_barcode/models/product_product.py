from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    main_category_id = fields.Many2one('main.category')
    vendor_category_id = fields.Many2one('vendor.category')
    sub_category_id = fields.Many2one('sub.category')
    serial_category_id = fields.Many2one('serial.category')

    @api.onchange('main_category_id', 'vendor_category_id', 'sub_category_id', 'serial_category_id')
    def _onchange_generate_barcode(self):
        main_category = self.main_category_id.id
        vendor_category = self.vendor_category_id.id
        sub_category = self.sub_category_id.id
        serial_category = self.serial_category_id.id

        if main_category and vendor_category and sub_category and serial_category:
            barcode = '-'.join([
                main_category and self.env['main.category'].browse(main_category).serial,
                vendor_category and self.env['vendor.category'].browse(vendor_category).serial,
                sub_category and self.env['sub.category'].browse(sub_category).serial,
                serial_category and self.env['serial.category'].browse(serial_category).serial,
            ])
            self.barcode = barcode
            product_name = ' '.join([
                main_category and self.env['main.category'].browse(main_category).name,
                vendor_category and self.env['vendor.category'].browse(vendor_category).name,
                sub_category and self.env['sub.category'].browse(sub_category).name,
                serial_category and self.env['serial.category'].browse(serial_category).name,
            ])
            self.name = product_name
