from odoo import fields, models, api


class Picking(models.Model):
    _inherit = "stock.picking"
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        compute='_compute_analytic_account_id',
        required=False)

    def _compute_analytic_account_id(self):
        for picking in self:
            picking.analytic_account_id = self.sale_id.analytic_account_id
    def button_validate(self):
        result = super().button_validate()
        # for move in self.move_lines:
        #     move.analytic_account_line_id = self.analytic_account_id.id
        return result