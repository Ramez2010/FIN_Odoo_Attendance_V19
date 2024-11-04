# Part of Softhealer Technologies.
from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.attendance"

    #inherited hr.attendance model and added new fields
    message_in = fields.Char('Check in message')
    message_out = fields.Char('Check out message')
    in_latitude = fields.Char("Latitude ")
    in_longitude = fields.Char("Longitude ")
    out_latitude = fields.Char("Latitude")
    out_longitude = fields.Char("Longitude")
    check_in_url = fields.Char("Open Check-in location in Google Maps")
    check_out_url = fields.Char("Open Check-out location in Google Maps")
