from odoo import models, fields, api, exceptions


class PayslipOvertime(models.Model):
    _inherit = 'hr.payslip'

    overtime_due = fields.Integer(string='Overtime due', compute='_compute_overtime_due')

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_overtime_due(self):
        for rec in self:
            overtime_requests = self.env['overtime.request'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('request_date', '>=', rec.date_from),
                ('request_date', '<=', rec.date_to),
                ('required_overtime_hours', '>=', 4),
                ('state', '=', 'approved')
            ])
            if overtime_requests:
                rec.overtime_due = len(overtime_requests)
            else:
                rec.overtime_due = 0
