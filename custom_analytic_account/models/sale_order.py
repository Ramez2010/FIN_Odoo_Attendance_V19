from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # analytic_account_id = fields.Many2one(
    #     'account.analytic.account',
    #     'Analytic Account',
    #     copy=False,
    #     store=True,
    # )

    # project_id = fields.Many2one(
    #     'project.project',
    #     ' Project',
    # )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id:
            return {'domain': {'analytic_account_id': []}}

        return {
            'domain': {'analytic_account_id': [('partner_id', '=', self.partner_id.id)]}
        }

    # @api.depends('project_id')
    # def _compute_analytic_account_id(self):
    #     for rec in self:
    #         if rec.project_id:
    #             rec.analytic_account_id = rec.project_id.analytic_account_id

    def _prepare_invoice(self):
        invoice_values = super()._prepare_invoice()
        if self.analytic_account_id:
            invoice_values['analytic_account_id'] = self.analytic_account_id.id
        return invoice_values

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        if self.analytic_account_id:
            moves.write({'analytic_account_id': self.analytic_account_id.id})
            for line in moves.line_ids:
                line.write({'analytic_account_id': self.analytic_account_id.id})
        return moves