from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    arabic_name = fields.Char(related='product_id.arabic_name')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    arabic_name = fields.Char(related='product_id.arabic_name')
