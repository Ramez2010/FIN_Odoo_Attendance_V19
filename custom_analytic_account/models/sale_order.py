from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
        copy=False,
        domain="[('partner_id', '=',partner_id)]",
    )

    def _prepare_invoice(self, *args, **kwargs):
        invoice_values = super()._prepare_invoice(*args, **kwargs)
        invoice_values['analytic_account_id'] = self.analytic_account_id.id
        return invoice_values

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        moves.analytic_account_id = self.analytic_account_id
        for line in moves.line_ids:
            line.analytic_account_id = self.analytic_account_id.id
        return moves

    @api.onchange('partner_id')
    def select_analytic_account_id(self):
        print('select_analytic_account_id')
        for order in self:
            if order.partner_id:
                related_accounts = self.env['account.analytic.account'].search(
                    [
                        ('partner_id', '=', order.partner_id.id),
                    ])
                order.analytic_account_id = related_accounts[
                    -1] if related_accounts else None

    def default_get(self, fields_list):
        data = super(SaleOrder, self).default_get(fields_list)
        account = self.env['account.analytic.account'].search([
            ('partner_id', '=', self.partner_id.id)
        ])
        if account:
            data['analytic_account_id'] = account[0].id
        return data
