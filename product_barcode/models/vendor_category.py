from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VendorCategory(models.Model):
    _name = 'vendor.category'
    _description = 'Vendor Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)
    parent = fields.Many2one('main.category', required=True, string='Main Category')
    partner = fields.Many2one('res.partner')

    @api.depends('name', 'serial', 'parent.name', 'parent.serial')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            serial = record.serial

            parent_name = record.parent.name or ''
            parent_serial = record.parent.serial or ''

            if name and serial:
                record.display_name = f" {parent_name} - {parent_serial} / {name} - {serial}"
            else:
                record.display_name = name or serial or ""

    @api.model_create_multi
    def create(self, vals_list):

        records = super(VendorCategory, self).create(vals_list)

        for record in records:
            if record.parent:
                count = self.search_count([('parent', '=', record.parent.id)])
                record.serial = str(count).zfill(4)

        return records

    def unlink(self):
        product_templates = self.env['product.template'].search([('vendor_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Vendor Category because it is referenced by a product.")

        return super(VendorCategory, self).unlink()