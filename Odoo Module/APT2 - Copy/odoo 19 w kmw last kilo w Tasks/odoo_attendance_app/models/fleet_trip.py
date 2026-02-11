# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FleetTrip(models.Model):
    _name = "odoo.attendance.fleet.trip"
    _description = "Fleet Trip Management"
    _order = "trip_start_date_time desc"

    name = fields.Char(string="Trip Reference", compute='_compute_name', store=True)
    
    # Trip identification
    trip_start_date_time = fields.Datetime(string="Trip Start", required=True)
    trip_end_date_time = fields.Datetime(string="Trip End")
    
    # Driver and Vehicle
    driver_user_id = fields.Many2one(
        'res.users', 
        string="Driver", 
        required=True,
        help="Driver who completed this trip"
    )
    vehicle_id = fields.Many2one(
        'odoo.attendance.vehicle', 
        string="Vehicle", 
        required=True,
        help="Vehicle used for this trip"
    )
    
    # Project/Analytic tracking
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Analytic Account",
        help="Project or cost center for this trip"
    )
    
    # Location tracking
    start_google_maps_location = fields.Text(string="Start Location")
    end_google_maps_location = fields.Text(string="End Location")
    
    # Kilometrage tracking
    start_kilometrage = fields.Float(string="Start Kilometrage", required=True)
    end_kilometrage = fields.Float(string="End Kilometrage")
    kilometrage_difference = fields.Float(
        string="Distance Travelled",
        compute='_compute_kilometrage_difference',
        store=True
    )
    
    # Status and metadata
    state = fields.Selection([
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='in_progress')
    
    @api.depends('driver_user_id', 'trip_start_date_time')
    def _compute_name(self):
        for record in self:
            if record.driver_user_id and record.trip_start_date_time:
                date_str = record.trip_start_date_time.strftime('%Y-%m-%d')
                record.name = f"{record.driver_user_id.name} - {date_str}"
            else:
                record.name = "New Trip"
    
    @api.depends('start_kilometrage', 'end_kilometrage')
    def _compute_kilometrage_difference(self):
        for record in self:
            if record.start_kilometrage and record.end_kilometrage:
                record.kilometrage_difference = record.end_kilometrage - record.start_kilometrage
            else:
                record.kilometrage_difference = 0
    
    def action_complete_trip(self):
        self.write({'state': 'completed'})
    
    def action_cancel_trip(self):
        self.write({'state': 'cancelled'})
