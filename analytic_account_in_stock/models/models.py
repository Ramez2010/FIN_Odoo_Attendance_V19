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

    def button_update_analytic_account(self):
        for rec in self:
            if rec.analytic_account_id:
                account_move = self.env['account.move'].search(
                    ['|', '|', ('name', 'ilike', rec.name), ('ref', 'ilike', rec.name),
                     ('partner_id', 'ilike', rec.name)])
                # print("#######################  ", account_move)

                if account_move:
                    # print('account_move', account_move)
                    for acc in account_move:
                        if acc.line_ids:
                            for l in acc.line_ids:
                                if l.debit > 0:
                                    # l.analytic_account_id = rec.analytic_account_id.id
                                    l.analytic_distribution = {rec.analytic_account_id.id: 100, }

                    account_move.button_draft()
                    account_move.action_post()
                    rec.is_updated = True
                else:
                    raise UserError('there is no journal entry for this Delivery.!')


class AccountAsset(models.Model):
    _inherit = 'account.asset'
