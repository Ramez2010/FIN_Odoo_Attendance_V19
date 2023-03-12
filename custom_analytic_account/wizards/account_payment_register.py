from odoo import api, Command, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        required=False,
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        sale_order_id = self.env['account.move'].browse(
            self._context.get('active_id'))
        res['analytic_account_id'] = sale_order_id.analytic_account_id.id
        return res

    def _create_payments(self):
        payments = super()._create_payments()
        payments.analytic_account_id = self.analytic_account_id.id
        payments.invoice_line_ids.analytic_account_id = self.analytic_account_id.id
        return payments