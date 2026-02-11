from odoo import fields, models, api


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    employee_payment_type = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
    ], default='bank', tracking=True)


class PayslipInherit(models.Model):
    _inherit = 'hr.payslip'

    employee_payment_type = fields.Selection(related='employee_id.employee_payment_type')
