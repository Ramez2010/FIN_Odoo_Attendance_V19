from odoo import api, fields, models


class OperationType(models.Model):
    _inherit = 'stock.picking.type'

    is_return = fields.Boolean(
        required=False)
