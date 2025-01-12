from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    is_worker = fields.Boolean(string="Is Worker", compute='_compute_is_worker', store=True)
    working_hour = fields.Float(string="Hours per Day", compute='_compute_hours_per_day', store=True)

    timesheet_start_date = fields.Date(string="Start Date", compute='_get_config_settings')
    timesheet_end_date = fields.Date(string="End Date", compute='_get_config_settings')

    custom_amount = fields.Monetary(compute='_compute_custom_amount', string="Hour Rate")

    def _get_config_settings(self):
        config_settings = self.env['res.config.settings'].sudo().get_values()
        self.timesheet_start_date = config_settings.get('timesheet_start_date')
        self.timesheet_end_date = config_settings.get('timesheet_end_date')

    # @api.depends('employee_id', 'employee_id.contract_id.wage', 'timesheet_start_date', 'timesheet_end_date')
    def _compute_custom_amount(self):
        for line in self:
            work_entries = self.env['hr.work.entry'].search([
                ('employee_id', '=', line.employee_id.id),
                ('date_start', '>', fields.Datetime.to_datetime(line.timesheet_start_date)),
                ('date_start', '<', fields.Datetime.to_datetime(line.timesheet_end_date)),
                ('work_entry_type_id.name', '=', 'Attendance'),
            ])
            print(work_entries)
            print( fields.Datetime.to_datetime(line.timesheet_start_date))
            print( fields.Datetime.to_datetime(line.timesheet_end_date))
            duration = sum(work_entries.mapped('duration'))
            print(duration)

            line.custom_amount = line.employee_id.contract_id.wage / duration if duration > 0 else 0

    @api.depends('employee_id')
    def _compute_is_worker(self):
        for line in self:
            line.is_worker = line.employee_id.is_worker if line.employee_id else False

    @api.depends('employee_id')
    def _compute_hours_per_day(self):
        for line in self:
            if line.employee_id and line.employee_id.resource_calendar_id:
                line.working_hour = line.employee_id.resource_calendar_id.hours_per_day
            else:
                line.working_hour = 8  # Default to 8 hours if no schedule is found

    def _get_total_hours_for_day(self, employee, date):
        """
        Calculate the total hours spent by the employee on the given date.
        """
        lines = self.search([
            ('employee_id', '=', employee.id),
            ('date', '=', date)
        ])
        total_hours = sum(line.unit_amount for line in lines)
        return total_hours

    @api.model
    def create(self, vals):
        employee_id = vals.get('employee_id')
        date = vals.get('date')
        if employee_id and date:
            employee = self.env['hr.employee'].browse(employee_id)
            working_hour = employee.resource_calendar_id.hours_per_day if employee.resource_calendar_id else 8
            total_hours_for_day = self._get_total_hours_for_day(employee, date)
            if (vals.get('unit_amount', 0) + total_hours_for_day) > working_hour:
                raise ValidationError(f"Total logged hours for the day cannot exceed {working_hour:.2f} hours.")
        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        for record in self:
            employee_id = vals.get('employee_id', record.employee_id.id)
            date = vals.get('date', record.date)
            if employee_id and date:
                employee = self.env['hr.employee'].browse(employee_id)
                working_hour = employee.resource_calendar_id.hours_per_day if employee.resource_calendar_id else 8
                total_hours_for_day = self._get_total_hours_for_day(employee, date)
                unit_amount = vals.get('unit_amount', record.unit_amount)
                if (unit_amount + total_hours_for_day - record.unit_amount) > working_hour:
                    raise ValidationError(f"Total logged hours for the day cannot exceed {working_hour:.2f} hours.")
        return super(AccountAnalyticLine, self).write(vals)
