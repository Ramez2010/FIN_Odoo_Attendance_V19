from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SubCategory(models.Model):
    _name = 'sub.category'
    _description = 'Sub Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)
    parent = fields.Many2one('vendor.category', required=True, string='Manufacture Category')

    higher_parent = fields.Many2one(
        'main.category',
        compute='_get_higher_parent',
        string='Main Category',
        store=True
    )

    @api.depends('parent', 'parent.parent')
    def _get_higher_parent(self):
        for record in self:
            if record.parent and record.parent.parent:
                record.higher_parent = record.parent.parent
            else:
                record.higher_parent = False

    @api.depends('name', 'serial', 'parent.name', 'parent.serial', 'higher_parent.name', 'higher_parent.serial')
    def _compute_display_name(self):
        for record in self:
            name = record.name or ''
            serial = record.serial or ''

            parent_name = record.parent.name or ''
            parent_serial = record.parent.serial or ''

            higher_name = record.higher_parent.name or ''
            higher_serial = record.higher_parent.serial or ''

            if record.name and record.serial:
                record.display_name = f"{higher_name} - {higher_serial} / {parent_name} - {parent_serial} / {name} - {serial}"
            else:
                record.display_name = name or serial or ""

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SubCategory, self).create(vals_list)
        for record in records:
            if record.parent:
                count = self.search_count([('parent', '=', record.parent.id)])
                record.serial = str(count).zfill(4)
        return records

    def unlink(self):
        product_templates = self.env['product.template'].search([('sub_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Sub Category because it is referenced by a product.")
        return super(SubCategory, self).unlink()