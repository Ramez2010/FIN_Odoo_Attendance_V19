from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        compute='_compute_analytic_account_from_stock',
        store=True,
        readonly=True,
        required=False,
    )

    @api.depends('stock_move_ids', 'stock_move_ids.picking_id')
    def _compute_analytic_account_from_stock(self):
        for move in self:
            found_analytic = False

            if move.stock_move_ids:
                for stock_move in move.stock_move_ids:
                    if stock_move.picking_id and stock_move.picking_id.analytic_account_id:
                        found_analytic = stock_move.picking_id.analytic_account_id
                        break

            if not found_analytic and move.ref:
                picking = self.env['stock.picking'].sudo().search([
                    ('name', '=', move.ref)
                ], limit=1)
                if picking and picking.analytic_account_id:
                    found_analytic = picking.analytic_account_id

            if found_analytic:
                move.analytic_account_id = found_analytic.id
            else:
                if not move.analytic_account_id:
                    move.analytic_account_id = False
