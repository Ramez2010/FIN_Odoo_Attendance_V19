from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VendorCategory(models.Model):
    _name = 'vendor.category'
    _description = 'Vendor Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)
    parent = fields.Many2one('main.category', required=True, string='Main Category')
    partner = fields.Many2one('res.partner')

    @api.model
    def create(self, vals):
        # if vals.get('serial', 'New') == 'New':
        #     vals['serial'] = self.env['ir.sequence'].next_by_code('vendor.category.sequence') or 'New'
        # return super(VendorCategory, self).create(vals) 
        res = super(VendorCategory, self).create(vals)
        count = self.search_count([('parent', '=', res.parent.id)])
        res.serial = str(count).zfill(4)
        return res

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            serial = record.serial
            parent = record.parent.name
            parent_serial = record.parent.serial
            display_name = f" {parent} - {parent_serial} / {name} - {serial}" if name and serial else name or serial
            result.append((record.id, display_name))
        return result

    def unlink(self):
        product_templates = self.env['product.template'].search([('vendor_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Vendor Category because it is referenced by a product.")

        return super(VendorCategory, self).unlink()
