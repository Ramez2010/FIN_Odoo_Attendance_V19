from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        domain="[('partner_id', '=',partner_id)]",
        required=False,
    )

    @api.onchange('partner_id')
    def select_analytic_account_id(self):
        for payment in self:
            if payment.partner_id:
                related_accounts = self.env['account.analytic.account'].search(
                    [
                        ('partner_id', '=', payment.partner_id.id),
                    ], )
                payment.analytic_account_id = related_accounts[
                    -1] if related_accounts else None
