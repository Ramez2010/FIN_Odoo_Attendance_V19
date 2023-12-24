from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SubCategory(models.Model):
    _name = 'sub.category'
    _description = 'Sub Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)
    parent = fields.Many2one('vendor.category', required=True, string='Manufacture Category')
    higher_parent = fields.Many2one('main.category', compute='_get_higher_parent', string='Main Category')

    @api.depends('parent')
    def _get_higher_parent(self):
        for record in self:
            if record.parent and record.parent.parent:
                record.higher_parent = record.parent.parent
            else:
                record.higher_parent = False

    @api.model
    def create(self, vals):
        res = super(SubCategory, self).create(vals)
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
            higher_parent = record.higher_parent.name
            higher_parent_serial = record.higher_parent.serial
            display_name = f"{higher_parent} - {higher_parent_serial} / {parent} - {parent_serial} / {name} - {serial}" if name and serial else name or serial
            result.append((record.id, display_name))
        return result

    def unlink(self):
        product_templates = self.env['product.template'].search([('sub_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Sub Category because it is referenced by a product.")
        return super(SubCategory, self).unlink()
