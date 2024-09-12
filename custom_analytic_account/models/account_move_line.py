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
            vals = line._prepare_analytic_lines()
            for val in vals:
                if val['name'] == 'Timesheet Entry':
                    val['general_account_id'] = self.env['account.account'].browse(int(self.env[
                        'ir.config_parameter'].sudo().get_param(
                        'timesheet_accounting.timesheet_debit_account_id')))
            analytic_line_vals.extend(vals)
        if len(analytic_line_vals) > 0:
            analytic_lines = self.env['account.analytic.line'].create(analytic_line_vals)
            analytic_lines._compute_general_account_id()
