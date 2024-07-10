# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overtime_journal_id = fields.Many2one('account.journal', string='Overtime Journal')
    overtime_debit_account_id = fields.Many2one('account.account', string='Overtime Debit Account')
    overtime_credit_account_id = fields.Many2one('account.account', string='Overtime Credit Account')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('overtime_journal_id', self.overtime_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param('overtime_debit_account_id', self.overtime_debit_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param('overtime_credit_account_id', self.overtime_credit_account_id.id)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            overtime_journal_id=int(self.env['ir.config_parameter'].sudo().get_param('overtime_journal_id', default=0)),
            overtime_debit_account_id=int(self.env['ir.config_parameter'].sudo().get_param('overtime_debit_account_id', default=0)),
            overtime_credit_account_id=int(self.env['ir.config_parameter'].sudo().get_param('overtime_credit_account_id', default=0)),
        )
        return res
