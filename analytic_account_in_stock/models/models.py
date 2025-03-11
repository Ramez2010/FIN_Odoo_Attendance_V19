# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class CustomStockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=False,
                                          index=True,
                                          states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    def button_validate(self):
        picking = super(CustomStockPickingInherit, self).button_validate()
        for rec in self:
            if rec.analytic_account_id:
                account_move = self.env['account.move'].search(
                    ['|', '|', ('name', '=', rec.name), ('ref', 'ilike', rec.name),
                     ('partner_id', '=', rec.name)])
                if account_move:
                    for acc in account_move:
                        if acc.line_ids:
                            for l in acc.line_ids:
                                l.analytic_distribution = {
                                    rec.analytic_account_id.id: 100, } if l.debit > 0 and not rec.picking_type_id.is_return or l.credit > 0 and rec.picking_type_id.is_return else False

                    account_move.button_draft()
                    account_move.action_post()
        return picking

    is_updated = fields.Boolean()
    is_return_ref = fields.Boolean(compute='_compute_is_return_ref')

    @api.depends('origin')
    def _compute_is_return_ref(self):
        for rec in self:
            if 'return' in (rec.origin or '').lower():
                rec.is_return_ref = True
            else:
                rec.is_return_ref = False

    def button_update_analytic_account(self):
        for rec in self:
            if rec.analytic_account_id:
                account_move = self.env['account.move'].search(
                    ['|', '|', ('name', 'ilike', rec.name), ('ref', 'ilike', rec.name),
                     ('partner_id', 'ilike', rec.name)])

                if account_move:
                    for acc in account_move:
                        if acc.line_ids:
                            for line in acc.line_ids:
                                # Clear the analytic account on debit line before applying it to the credit line
                                if line.debit > 0:
                                    line.analytic_distribution = False

                                # Assign analytic account to the credit line
                                if line.credit > 0:
                                    line.analytic_distribution = {rec.analytic_account_id.id: 100}

                    # Re-post the account move after the update
                    account_move.button_draft()
                    account_move.action_post()
                    rec.is_updated = True
                else:
                    raise UserError('There is no journal entry for this Delivery.')

        return True


class AccountAsset(models.Model):
    _inherit = 'account.asset'
