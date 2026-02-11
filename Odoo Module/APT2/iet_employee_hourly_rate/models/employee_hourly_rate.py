from odoo import models, fields, api
import calendar
from datetime import date

class EmployeeHourlyRate(models.Model):
    _name = 'employee.hourly.rate'
    _description = 'Employee Hourly Rate'

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True)
    employee_id = fields.Many2one(related='contract_id.employee_id', string='Employee', store=True)
    currency_id = fields.Many2one(string="Currency", related='contract_id.currency_id', readonly=True)
    wage = fields.Monetary(related='contract_id.wage', string='Basic Salary', store=True)

    date = fields.Date(string='Date', required=True)
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month', compute="_compute_month",store=True)
    year = fields.Char(string='Year', compute="_compute_year", store=True)
    working_days = fields.Integer(string='Working Days', compute="_compute_working_days", store=True)
    hour_rate = fields.Float(string='Hourly Rate', compute='_compute_hour_rate', store=True)

    @api.depends('date')
    def _compute_month(self):
        for record in self:
            if record.date:
                record.month = str(record.date.month)

    @api.depends('date')
    def _compute_year(self):
        for record in self:
            if record.date:
                record.year = str(record.date.year)

    @api.depends('date')
    def _compute_working_days(self):
        for record in self:
            year = record.date.year
            month = record.date.month
            total_days = calendar.monthrange(year, month)[1]
            count = 0
            for day in range(1, total_days + 1):
                current_date = date(year, month, day)
                if current_date.weekday() != 4 and current_date.weekday() != 5:  # 4 = Friday, 5 = Saturday
                    count += 1

            record.working_days = count

    @api.depends('working_days', 'contract_id', 'wage')
    def _compute_hour_rate(self):
        for record in self:
            if record.employee_id and record.contract_id and record.working_days:
                record.hour_rate = record.wage / record.working_days / 8
            else:
                record.hour_rate = 0.0