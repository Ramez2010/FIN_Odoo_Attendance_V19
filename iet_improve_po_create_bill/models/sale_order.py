from odoo import models, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("order_id", "product_id")
    def _onchange_set_analytic_distribution_from_so(self):
        for line in self:
            order = line.order_id
            if (
                order.analytic_account_id
                and not line.analytic_distribution
            ):
                line.analytic_distribution = {
                    str(order.analytic_account_id.id): 100
                }
