# from odoo import models, fields, api, _
#
# class AnalyticAccountInherit(models.Model):
#     _name = 'analytic.account.id'
#     _description = 'Analytic Account ID'
#
#     name = fields.Char("ID", required=True)
#     analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", required=True)
#
#     @api.onchange('analytic_account_id')
#     def _onchange_analytic_account_id(self):
#         if self.analytic_account_id:
#             self.name = self.analytic_account_id.code  # Update the name if the analytic account is changed