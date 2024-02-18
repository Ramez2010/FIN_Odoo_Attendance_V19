from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    custom_quantity = fields.Float()
    total_quantity = fields.Float(compute='get_total_quantity', store=True)

    @api.depends('custom_quantity', 'product_qty')
    def get_total_quantity(self):
        for rec in self:
            if rec.product_qty and rec.custom_quantity:
                rec.total_quantity = rec.product_qty / rec.custom_quantity
            else:
                rec.total_quantity = 0


class StockQuantity(models.Model):
    _inherit = 'stock.quant'

    total_quantity = fields.Float(related='lot_id.total_quantity')
