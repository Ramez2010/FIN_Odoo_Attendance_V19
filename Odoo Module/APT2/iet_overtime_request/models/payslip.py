from odoo import models, fields, api


class PayslipOvertime(models.Model):
    _inherit = 'hr.payslip'

    overtime_due = fields.Integer(string='Overtime due', compute='_compute_overtime_due', store=True)

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_overtime_due(self):
        OvertimeRequest = self.env.get('overtime.request')

        for rec in self:
            rec.overtime_due = 0

            if not OvertimeRequest or not rec.employee_id or not rec.date_from or not rec.date_to:
                continue

            count = OvertimeRequest.search_count([
                ('employee_id', '=', rec.employee_id.id),
                ('request_date', '>=', rec.date_from),
                ('request_date', '<=', rec.date_to),
                ('required_overtime_hours', '>=', 4),
                ('state', '=', 'approved')
            ])

            rec.overtime_due = count
