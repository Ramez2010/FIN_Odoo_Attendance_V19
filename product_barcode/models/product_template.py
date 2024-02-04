from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    main_category_id = fields.Many2one('main.category')
    vendor_category_id = fields.Many2one('vendor.category')
    sub_category_id = fields.Many2one('sub.category')
    serial_category_id = fields.Many2one('serial.category')
    check = fields.Boolean(default=False, string="check")

    def generate_product_name(self):
        for rec in self:
            rec.check = False
            rec._onchange_generate_barcode()

    @api.onchange('main_category_id', 'vendor_category_id', 'sub_category_id', 'serial_category_id')
    def _onchange_generate_barcode(self):
        for rec in self:
            main_category = rec.main_category_id.id
            vendor_category = rec.vendor_category_id.id
            sub_category = rec.sub_category_id.id
            serial_category = rec.serial_category_id.id
            check = rec.check
            if main_category and vendor_category and sub_category and serial_category and check == False:
                barcode = '-'.join([
                    main_category and rec.env['main.category'].browse(main_category).serial,
                    vendor_category and rec.env['vendor.category'].browse(vendor_category).serial,
                    sub_category and rec.env['sub.category'].browse(sub_category).serial,
                    serial_category and rec.env['serial.category'].browse(serial_category).serial,
                ])
                rec.barcode = barcode
                product_name = ' '.join([
                    main_category and rec.env['main.category'].browse(main_category).name,
                    vendor_category and rec.env['vendor.category'].browse(vendor_category).name,
                    sub_category and rec.env['sub.category'].browse(sub_category).name,
                    serial_category and rec.env['serial.category'].browse(serial_category).name,
                ])
                rec.name = product_name
                rec.check = True


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order', string='Sale Order')
