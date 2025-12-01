from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SerialCategory(models.Model):
    _name = 'serial.category'
    _description = 'Serial Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)
    parent = fields.Many2one('sub.category', required=True, string='Sub Category')

    higher_parent = fields.Many2one(
        'vendor.category',
        compute='_get_higher_parent',
        string='Manufacture Category',
        store=True
    )

    main_category = fields.Many2one(
        'main.category',
        compute='_get_main_category',
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

    @api.depends('higher_parent', 'higher_parent.parent')
    def _get_main_category(self):
        for record in self:
            if record.higher_parent and record.higher_parent.parent:
                record.main_category = record.higher_parent.parent
            else:
                record.main_category = False

    @api.depends('name', 'serial')
    def _compute_display_name(self):
        for record in self:
            name = record.name or ''
            serial = record.serial or ''
            if record.name and record.serial:
                record.display_name = f"{name} - {serial}"
            else:
                record.display_name = name or serial or ""

    @api.model_create_multi
    def create(self, vals_list):
        records = super(SerialCategory, self).create(vals_list)
        for record in records:
            if record.parent:
                count = self.search_count([('parent', '=', record.parent.id)])
                record.serial = str(count).zfill(4)
        return records

    def unlink(self):
        product_templates = self.env['product.template'].search([('serial_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Serial Category because it is referenced by a product.")
        return super(SerialCategory, self).unlink()