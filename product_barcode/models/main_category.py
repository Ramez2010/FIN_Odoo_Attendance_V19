from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MainCategory(models.Model):
    _name = 'main.category'
    _description = 'Main Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)

    @api.depends('name', 'serial')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            serial = record.serial
            if name and serial:
                record.display_name = f"{name} - {serial}"
            else:
                record.display_name = name or serial or ""

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('serial', 'New') == 'New':
                vals['serial'] = self.env['ir.sequence'].next_by_code('main.category.sequence') or 'New'
        return super(MainCategory, self).create(vals_list)

    def unlink(self):
        product_templates = self.env['product.template'].search([('main_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Main Category because it is referenced by a product.")
        return super(MainCategory, self).unlink()
