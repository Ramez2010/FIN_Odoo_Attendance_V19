from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    #leaves_days = fields.Selection([('one', 'One Day Leaves'), ('two', 'Two Days Leaves')])
    overtime_rate = fields.Float(string='Overtime Rate/hour', store=True)
