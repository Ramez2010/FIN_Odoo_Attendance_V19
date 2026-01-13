from odoo import models


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
