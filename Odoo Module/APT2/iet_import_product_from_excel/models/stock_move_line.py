from odoo import models, fields, api


class StockMoveLineInherit(models.Model):
    _inherit = 'stock.move.line'

    lot_2 = fields.Many2one('stock.lot')
    lot_name = fields.Char(related='lot_2.name')
