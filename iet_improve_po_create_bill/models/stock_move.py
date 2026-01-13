from odoo import models,fields,api,_


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        AccountMoveLine = self.env['account.move.line']
        for picking in self:
            if picking.picking_type_id.code == 'internal':

                analytic_account = picking.analytic_account_id
                if not analytic_account:
                    continue
                dest_account = picking.picking_type_id.default_location_dest_id.valuation_account_id
                if not dest_account:
                    continue
                lines = AccountMoveLine.search([
                    ('account_id', '=', dest_account.id),
                    '|', ('name', '=', picking.name), ('ref', '=', picking.name)
                ])

                for line in lines:
                    if line.account_id.account_type.startswith('expense'):
                        line.analytic_distribution = {str(analytic_account.id): 100}

        return res



class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    allowed_products = fields.Many2many(
        'product.product',
        string="Allowed Products",
        compute='_compute_allowed_products'
    )

    @api.depends('product_return_moves.product_id')
    def _compute_allowed_products(self):
        for wizard in self:
            sale_products = wizard.picking_id.sale_id.order_line.mapped('product_id') if wizard.picking_id.sale_id else self.env['product.product']
            existing_lines_products = wizard.product_return_moves.mapped('product_id')
            wizard.allowed_products = sale_products - existing_lines_products
