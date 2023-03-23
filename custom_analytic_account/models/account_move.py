from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        related='stock_move_id.picking_id.analytic_account_id',
        required=False,
    )
