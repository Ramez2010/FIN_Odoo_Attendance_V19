from odoo import api, fields, models


class AnalyticAccountLineCustom(models.Model):
    _name = 'account.analytic.line'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'account.analytic.line']

    name = fields.Char(tracking=True)
    ref = fields.Char(tracking=True)
    amount = fields.Monetary(tracking=True)
    date = fields.Date(tracking=True)
    unit_amount = fields.Float(tracking=True)

    @api.constrains('move_line_id')
    def _compute_general_account_id(self):
        for line in self:
            line.general_account_id = line.move_line_id.account_id
