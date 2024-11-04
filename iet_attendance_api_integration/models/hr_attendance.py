from odoo import fields, models, api, _


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    analytic_account_id = fields.Many2one("account.analytic.account", string="Account Analytic")