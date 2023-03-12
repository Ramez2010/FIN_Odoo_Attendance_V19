from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        related='move_id.analytic_account_id',
        required=False,
    )
