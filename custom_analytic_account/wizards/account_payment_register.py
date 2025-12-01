from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        required=False,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self._context.get('active_ids') or [self._context.get('active_id')]

        if active_ids:
            move = self.env['account.move'].browse(active_ids[0])
            if move.exists() and hasattr(move, 'analytic_account_id') and move.analytic_account_id:
                res['analytic_account_id'] = move.analytic_account_id.id
        return res

    def _create_payments(self):
        payments = super()._create_payments()

        if self.analytic_account_id:
            payments.write({'analytic_account_id': self.analytic_account_id.id})

            for payment in payments:
                if payment.move_id:
                    payment.move_id.write({'analytic_account_id': self.analytic_account_id.id})

        return payments