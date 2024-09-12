from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        related='move_id.analytic_account_id',
        required=False,
    )

    #

    def _create_analytic_lines(self):
        """ Create analytic items upon validation of an account.move.line having an analytic distribution.
        """
        self._validate_analytic_distribution()
        analytic_line_vals = []
        for line in self:
            analytic_line_vals.extend(line._prepare_analytic_lines())

        analytic_lines = self.env['account.analytic.line'].create(analytic_line_vals)
        analytic_lines._compute_general_account_id()
