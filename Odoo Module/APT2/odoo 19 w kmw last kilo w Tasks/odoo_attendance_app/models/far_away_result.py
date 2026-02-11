# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FarAwayResult(models.Model):
    _name = 'odoo.attendance.far.away.result'
    _description = 'Far-away Alert Result'
    _order = 'timestamp desc'

    timestamp = fields.Datetime(
        string='Detected At',
        default=fields.Datetime.now,
        required=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
    )
    employee_app_id = fields.Many2one(
        'odoo.attendance.employee',
        string='App Account',
        ondelete='set null',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        ondelete='set null',
    )
    allowed_radius_km = fields.Float(string='Allowed Radius (km)')
    actual_distance_km = fields.Float(string='Actual Distance (km)')
    excess_km = fields.Float(string='Exceeded By (km)')
    project_latitude = fields.Float(string='Project Latitude')
    project_longitude = fields.Float(string='Project Longitude')
    current_latitude = fields.Float(string='Current Latitude')
    current_longitude = fields.Float(string='Current Longitude')
    location_timestamp = fields.Datetime(string='Employee Location Timestamp')

    @api.depends('current_latitude', 'current_longitude')
    def _compute_current_location_url(self):
        for record in self:
            if record.current_latitude and record.current_longitude:
                record.current_location_url = (
                    'https://www.google.com/maps/search/?api=1&query='
                    f'{record.current_latitude:.6f}%2C{record.current_longitude:.6f}'
                )
            else:
                record.current_location_url = False

    current_location_url = fields.Char(
        string='Current Location',
        compute='_compute_current_location_url',
        help='Google Maps link for the employee location.',
    )
