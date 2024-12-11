from odoo import models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    is_worker = fields.Boolean(string="Is worker?")


class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    is_worker = fields.Boolean(related='employee_id.is_worker',string="Is worker?")
    employee_payment_type = fields.Selection(string="Employee Payment Type",related='employee_id.employee_payment_type')
