# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    analytic_account_ref_id = fields.Char("ID", related="analytic_account_id.code", tracking=True, store=True)


# class StockPicking(models.Model):
#     _inherit = 'stock.picking'
#
#     analytic_account_reference = fields.Many2one(
#         'analytic.account.id',
#         string='Analytic Account ID',
#         states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}
#     )
#
#     analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=False,
#                                           index=True, compute="_get_analytic_account_id", store=True
#                                           )
#
#     @api.depends('analytic_account_reference')
#     def _get_analytic_account_id(self):
#         for rec in self:
#             if rec.analytic_account_reference:
#                 rec.analytic_account_id = rec.analytic_account_reference.analytic_account_id
#             else:
#                 rec.analytic_account_id = False

    # @api.onchange('analytic_account_reference')
    # def _onchange_analytic_account_reference(self):
    #     for rec in self:
    #         if rec.analytic_account_reference:
    #             analytic_account_id = self.env['account.analytic.account'].search([
    #                 ('code', '=', rec.analytic_account_reference.name)
    #             ])
    #             # Set analytic_account_id only if an analytic account reference is selected
    #             if analytic_account_id:
    #                 rec.analytic_account_id = analytic_account_id

    # @api.model
    # def create(self, vals):
    #     if 'analytic_account_reference' in vals:
    #         analytic_account = self.env['account.analytic.account'].search([
    #             ('reference', '=', vals['analytic_account_reference'])
    #         ], limit=1)
    #         if analytic_account:
    #             vals['analytic_account_id'] = analytic_account.id
    #     return super(StockPicking, self).create(vals)
    #
    # def write(self, vals):
    #     if 'analytic_account_reference' in vals:
    #         analytic_account = self.env['account.analytic.account'].search([
    #             ('reference', '=', vals['analytic_account_reference'])
    #         ], limit=1)
    #         if analytic_account:
    #             vals['analytic_account_id'] = analytic_account.id
    #     return super(StockPicking, self).write(vals)
