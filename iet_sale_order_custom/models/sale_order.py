from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    employee = fields.Many2one('hr.employee')
    def action_confirm(self):
        if not self.analytic_account_id:
            raise ValidationError("The Analytic Account Field Must Be Set")
        else:
            return super(SaleOrder, self).action_confirm()
