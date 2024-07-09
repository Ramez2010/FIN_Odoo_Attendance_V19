from odoo import models, fields, api

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    is_worker = fields.Boolean(string="Is Worker", compute='_compute_is_worker', store=True)

    @api.depends('employee_id')
    def _compute_is_worker(self):
        for line in self:
            line.is_worker = line.employee_id.is_worker if line.employee_id else False
