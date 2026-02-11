# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AnalyticAccountInherit(models.Model):
    _inherit = 'account.analytic.account'

    code = fields.Char("ID", default=lambda self: _('New'),
       copy=False, readonly=True, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = (self.env['ir.sequence'].
                                  next_by_code('analytic.account.sequence'))
        result = super().create(vals_list)
        # self.env['analytic.account.id'].create({
        #     'name': result.code,
        #     'analytic_account_id': result.id
        # })
        return result

    def action_set_analytic_account_sequence_code(self):
        for record in self:
            if not record.code:
                code = (self.env['ir.sequence'].
                                  next_by_code('analytic.account.sequence'))
                record.write({'code': code})
                # self.env['analytic.account.id'].create({
                #     'name': record.code,
                #     'analytic_account_id': record.id
                # })

