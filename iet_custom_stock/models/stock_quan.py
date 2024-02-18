from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    arabic_name = fields.Char(related='product_id.arabic_name')
