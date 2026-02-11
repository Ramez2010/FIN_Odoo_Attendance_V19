# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class HrEmployeeLocationLatest(models.Model):
    _name = 'hr.employee.location.latest'
    _description = 'Employee Latest Live Location'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade')
    latitude = fields.Float(string='Latitude', digits=(10, 7), required=True)
    longitude = fields.Float(string='Longitude', digits=(10, 7), required=True)
    accuracy = fields.Float(string='Accuracy (m)')
    timestamp_utc = fields.Datetime(string='Timestamp (UTC)', required=True, default=fields.Datetime.now)
    source = fields.Selection([
        ('mobile', 'Mobile App'),
        ('provider', 'Tracking Provider'),
        ('manual', 'Manual'),
    ], string='Source', default='mobile')

    reachable_status = fields.Selection([
        ('reachable', 'Reachable'),
        ('unreachable', 'Not Reachable'),
    ], string='Status', compute='_compute_reachable_status')
    
    unreachable_reason = fields.Char(string='Reason', compute='_compute_reachable_status')

    _sql_constraints = [
        ('unique_employee_location', 'UNIQUE(employee_id)', 'Each employee can have only one latest location record.')
    ]

    @api.depends('timestamp_utc', 'employee_id.attendance_state')
    def _compute_reachable_status(self):
        for record in self:
            if record.employee_id and record.employee_id.attendance_state != 'checked_in':
                record.reachable_status = 'unreachable'
                record.unreachable_reason = 'Employee not checked-in'
                continue

            if not record.timestamp_utc:
                record.reachable_status = 'unreachable'
                record.unreachable_reason = 'No location data'
                continue

            record.reachable_status = 'reachable'
            record.unreachable_reason = False
