from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MainCategory(models.Model):
    _name = 'main.category'
    _description = 'Main Category'

    name = fields.Char(string='Name')
    serial = fields.Char(string='Serial', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        if vals.get('serial', 'New') == 'New':
            vals['serial'] = self.env['ir.sequence'].next_by_code('main.category.sequence') or 'New'
        return super(MainCategory, self).create(vals)

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            serial = record.serial
            display_name = f"{name} - {serial}" if name and serial else name or serial
            result.append((record.id, display_name))
        return result

    def unlink(self):
        product_templates = self.env['product.template'].search([('main_category_id', 'in', self.ids)])
        if product_templates:
            raise ValidationError("Cannot delete Main Category because it is referenced by a product.")

        return super(MainCategory, self).unlink()
