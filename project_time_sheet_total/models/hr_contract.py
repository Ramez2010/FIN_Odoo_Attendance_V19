from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    #leaves_days = fields.Selection([('one', 'One Day Leaves'), ('two', 'Two Days Leaves')])
    overtime_rate = fields.Float(string='Overtime Rate/hour', store=True)
    soci_emp = fields.Float(string='Social Insurance Employee', store=True)
    soci_comp = fields.Float(string='Social Insurance Company', store=True)
    medical_ins_emp = fields.Float(string='Medical Insurance Employee', store=True)
    medical_ins_comp = fields.Float(string='Medical Insurance Company', store=True)

