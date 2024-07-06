from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    timesheet_journal_id = fields.Many2one('account.journal', string="Journal")
    timesheet_debit_account_id = fields.Many2one('account.account', string="Debit Account")
    timesheet_credit_account_id = fields.Many2one('account.account', string="Credit Account")
    timesheet_start_date = fields.Date(string="Start Date")
    timesheet_end_date = fields.Date(string="End Date")


    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        timesheet_journal_id = params.get_param('timesheet_accounting.timesheet_journal_id', default=False)
        timesheet_debit_account_id = params.get_param('timesheet_accounting.timesheet_debit_account_id', default=False)
        timesheet_credit_account_id = params.get_param('timesheet_accounting.timesheet_credit_account_id', default=False)
        timesheet_start_date = params.get_param('timesheet_accounting.timesheet_start_date', default=False)
        timesheet_end_date = params.get_param('timesheet_accounting.timesheet_end_date', default=False)

        res.update(
            timesheet_journal_id=int(timesheet_journal_id) if timesheet_journal_id else False,
            timesheet_debit_account_id=int(timesheet_debit_account_id) if timesheet_debit_account_id else False,
            timesheet_credit_account_id=int(timesheet_credit_account_id) if timesheet_credit_account_id else False,
            timesheet_start_date=timesheet_start_date,
            timesheet_end_date=timesheet_end_date,
        )
        print("xxxxxxxxxx", res)
        return res


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()

        params.set_param('timesheet_accounting.timesheet_journal_id', self.timesheet_journal_id.id)
        params.set_param('timesheet_accounting.timesheet_debit_account_id', self.timesheet_debit_account_id.id)
        params.set_param('timesheet_accounting.timesheet_credit_account_id', self.timesheet_credit_account_id.id)
        params.set_param('timesheet_accounting.timesheet_start_date', self.timesheet_start_date)
        params.set_param('timesheet_accounting.timesheet_end_date', self.timesheet_end_date)

    def _generate_journal_entries(self):
        start_date = self.env['ir.config_parameter'].sudo().get_param('timesheet_accounting.timesheet_start_date')
        end_date = self.env['ir.config_parameter'].sudo().get_param('timesheet_accounting.timesheet_end_date')
        journal_id = self.env['ir.config_parameter'].sudo().get_param('timesheet_accounting.timesheet_journal_id')
        jour_obj = self.env['account.journal'].search([('id','=',journal_id)])
        currency_id = jour_obj.currency_id.id
        debit_account_id = self.env['ir.config_parameter'].sudo().get_param(
            'timesheet_accounting.timesheet_debit_account_id')
        credit_account_id = self.env['ir.config_parameter'].sudo().get_param(
            'timesheet_accounting.timesheet_credit_account_id')

        timesheets = self.env['account.analytic.line'].search([
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])
        print('timesheets',timesheets)

        projects = timesheets.mapped('project_id')
        for project in projects:
            project_timesheets = timesheets.filtered(lambda t: t.project_id == project)
            amount = sum(project_timesheets.mapped('amount'))

            move_vals = {
                'journal_id': jour_obj.id,
                'move_type': 'entry',
                'ref':project.name,
                'date': fields.Date.context_today(self),
                'currency_id': currency_id if currency_id else 1,
                'line_ids': [
                    (0, 0, {
                        'name': 'Timesheet Entry',
                        'account_id': debit_account_id,
                        'analytic_distribution': {project.analytic_account_id.id:100},
                        'debit': amount,
                        'credit': 0,
                    }),
                    (0, 0, {
                        'name': 'Timesheet Entry',
                        'account_id': credit_account_id,
                        'analytic_distribution': {project.analytic_account_id.id:100},
                        'debit': 0,
                        'credit': amount,
                    }),
                ],
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()