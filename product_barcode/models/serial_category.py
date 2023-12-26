from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SerialCategory(models.Model):
    _name = 'serial.category'
    _description = 'Serial Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)
    parent = fields.Many2one('sub.category', required=True, string='Sub Category')
    higher_parent = fields.Many2one('vendor.category', compute='_get_higher_parent', string='Manufacture Category')
    main_category = fields.Many2one('main.category', compute='_get_main_category')

    @api.depends('parent')
    def _get_higher_parent(self):
        for record in self:
            if record.parent and record.parent.parent:
                record.higher_parent = record.parent.parent
            else:
                record.higher_parent = False

    @api.depends('higher_parent')
    def _get_main_category(self):
        for record in self:
            if record.parent and record.parent.parent:
                record.main_category = record.higher_parent.parent
            else:
                record.main_category = False

    @api.model
    def create(self, vals):
        res = super(SerialCategory, self).create(vals)
        count = self.search_count([('parent', '=', res.parent.id)])
        res.serial = str(count).zfill(4)
        return res

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            serial = record.serial
            display_name = f"{name} - {serial}" if name and serial else name or serial
            result.append((record.id, display_name))
        return result

    def unlink(self):
        product_templates = self.env['product.template'].search([('serial_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Serial Category because it is referenced by a product.")
        return super(SerialCategory, self).unlink()
