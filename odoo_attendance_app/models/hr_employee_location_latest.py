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
        # Freshness window in minutes from config (default 2)
        timeout_minutes = int(self.env['ir.config_parameter'].sudo().get_param(
            'odoo_attendance_app.live_location_timeout_minutes', '15'))
        limit_time = fields.Datetime.now() - timedelta(minutes=timeout_minutes)
        
        for record in self:
            # If employee is not checked in, treat as unreachable (explicit)
            if record.employee_id and record.employee_id.attendance_state != 'checked_in':
                record.reachable_status = 'unreachable'
                record.unreachable_reason = 'Employee not checked-in'
                continue

            if not record.timestamp_utc:
                record.reachable_status = 'unreachable'
                record.unreachable_reason = 'No location data'
                continue

            if record.timestamp_utc < limit_time:
                record.reachable_status = 'unreachable'
                record.unreachable_reason = 'No recent location update'
            else:
                record.reachable_status = 'reachable'
                record.unreachable_reason = False
