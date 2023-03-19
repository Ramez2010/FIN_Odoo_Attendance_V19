from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(
        self,
        qty,
        cost,
        credit_account_id,
        debit_account_id,
        svl_id,
        description,
    ):
        res = super()._prepare_account_move_line(
            qty,
            cost,
            credit_account_id,
            debit_account_id,
            svl_id,
            description,
        )
        if self.picking_id.analytic_account_id:
            for line in res:
                line[-1][
                    'analytic_account_id'] = self.picking_id.analytic_account_id.id
                line[-1]['analytic_distribution'] = {
                    self.picking_id.analytic_account_id.id: 0.0
                }
        return res
