# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools import float_compare, float_round
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class HrPayrollInherit(models.Model):
    _inherit = "hr.payslip"

    timesheet_lines = fields.Many2many(
        'account.analytic.line',
        compute='_compute_timesheet_lines',
        string='Timesheet Lines'
    )
    timesheet_hours = fields.Float(
        string='Timesheet Hours',
        compute='_compute_timesheet_hours',
        store=False
    )
    hours_shortfall = fields.Float(
        compute='_compute_hours_shortfall',
        store=False
    )

    progress = fields.Float(
        compute='_compute_progress',
        store=False,)
    timesheet_cost = fields.Float(
        string="Timesheet Cost",
        default=0.0,
        compute='_compute_timesheet_hours_cost',
        store=False)
    attendance_hours = fields.Float(string='Attendance Work Hours', compute='_compute_attendance_hours', store=True)
    required_hours = fields.Float(string='Required Hours', compute='_compute_required_hours', store=True)
    all_lines = fields.Char(string="All Lines")
    task_time = fields.Float(default=0.0)
    overtime_hours = fields.Float(compute="get_overtime_hours", store=False)
    overtime_cost = fields.Float(string="Overtime Cost", default=0.0, compute='_compute_overtime_hours_cost',store=False)
    worked_days_hours = fields.Float(string='Worked Days Hours', compute='_compute_worked_days_hours', store=True)

    @api.onchange('employee_id', 'date_from', 'date_to', 'timesheet_lines', 'version_id', 'contract_id.resource_calendar_id.full_time_required_hours')
    def _compute_required_hours(self):
        for rec in self:
            if rec.version_id and rec.version_id.resource_calendar_id:
                rec.required_hours = rec.version_id.resource_calendar_id.full_time_required_hours * 4  # Hours/week multiplied by number of weeks (4)
            else:
                rec.required_hours = 0.0

    @api.depends('worked_days_hours')  # Depend on worked_days_hours instead of employee_id
    def _compute_attendance_hours(self):
        for record in self:
            record.attendance_hours = record.worked_days_hours

    @api.depends('timesheet_lines', 'timesheet_lines.date')
    def _compute_timesheet_lines(self):
        for record in self:
            if record.employee_id and record.date_from and record.date_to:
                record.timesheet_lines = self.env['account.analytic.line'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('date', '>=', record.date_from),
                    ('date', '<=', record.date_to)
                ])
            else:
                record.timesheet_lines = self.env['account.analytic.line']

    @api.depends('timesheet_lines.unit_amount', 'task_time')
    def _compute_work_hours(self):
        for record in self:
            record.timesheet_hours = sum(line.unit_amount for line in record.timesheet_lines if line.unit_amount > 0)
            record.hours_shortfall = max(0, record.required_hours - record.timesheet_hours) + max(0, record.task_time)
            record.progress = (100.0 * record.timesheet_hours / record.required_hours) if record.required_hours else 0.0

    # @api.depends('timesheet_hours', 'attendance_hours')
    # def get_overtime_hours(self):
    #     for rec in self:
    #         rec.overtime_hours = rec.timesheet_hours - rec.attendance_hours if rec.timesheet_hours > rec.attendance_hours else 0.0
    @api.depends('employee_id', 'date_from', 'date_to')
    def get_overtime_hours(self):
        for rec in self:
            overtime_requests = self.env['overtime.request'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('request_date', '>=', rec.date_from),
                ('request_date', '<=', rec.date_to),
                ('state', '=', 'approved')
            ])
            if overtime_requests:
                rec.overtime_hours = sum(request.required_overtime_hours for request in overtime_requests)
            else:
                rec.overtime_hours = 0
    @api.depends('worked_days_line_ids.number_of_hours')
    def _compute_worked_days_hours(self):
        for record in self:
            worked_days_hours = sum(line.number_of_hours for line in record.worked_days_line_ids)
            record.worked_days_hours = worked_days_hours

    @api.depends('overtime_hours')
    def _compute_overtime_hours_cost(self):
        for rec in self:
            rec.overtime_cost = rec.overtime_hours * rec.employee_id.version_id.overtime_rate
    @api.depends('timesheet_hours')
    def _compute_timesheet_hours_cost(self):
        for rec in self:
            rec.timesheet_cost = rec.timesheet_hours * rec.employee_id.hourly_cost