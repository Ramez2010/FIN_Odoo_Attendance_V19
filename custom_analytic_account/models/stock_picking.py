from odoo import fields, models, api


class Picking(models.Model):
    _inherit = "stock.picking"
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
    )

    @api.depends('partner_id')
    def _compute_analytic_account_id(self):
        for picking in self:
            picking.analytic_account_id = False
            if self.sale_id:
                picking.analytic_account_id = self.sale_id.analytic_account_id
            elif picking.partner_id:
                related_accounts = self.env['account.analytic.account'].search(
                    [('partner_id', '=', picking.partner_id.id)])
                picking.analytic_account_id = related_accounts[
                    -1] if related_accounts else None

    def button_validate(self):
        result = super().button_validate()
    #     for line in self.move_ids.move_line_ids:
    #         # if line.display_type == 'product' or not line.move_id.is_invoice(include_receipts=True):
    #         distribution = self.env['account.analytic.distribution.model']._get_distribution({
    #             "product_id": line.product_id.id,
    #             "product_categ_id": line.product_id.categ_id.id,
    #             "partner_id": self.partner_id.id,
    #             "partner_category_id": self.partner_id.category_id.ids,
    #             "account_prefix": self.analytic_account_id.code,
    #             "company_id": self.company_id.id,
    #         })
    #         line.analytic_distribution = distribution or line.analytic_distribution
    # # for move in self.move_line_ids:
    #     #     move.analytic_account_line_id = self.analytic_account_id.id
        return result