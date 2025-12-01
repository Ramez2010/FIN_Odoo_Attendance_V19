# Part of Softhealer Technologies.
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.attendance"

    #inherited hr.attendance model and added new fields
    check_in_url = fields.Char("Open Check-in location in Google Maps", compute="_compute_check_in_url")
    check_out_url = fields.Char("Open Check-out location in Google Maps", compute="_compute_check_out_url")


    @api.depends("in_latitude", "in_longitude")
    def _compute_check_in_url(self):
        for rec in self:
            if rec.in_latitude and rec.in_longitude:
                rec.check_in_url = "http://maps.google.com/maps?q=" + str(rec.in_latitude) + ',' + str(rec.in_longitude)
            else:
                rec.check_in_url = False

    @api.depends("out_latitude", "out_longitude")
    def _compute_check_out_url(self):
        for rec in self:
            if rec.out_latitude and rec.out_longitude:
                rec.check_out_url = "http://maps.google.com/maps?q=" + str(rec.out_latitude) + ',' + str(rec.out_longitude)
            else:
                rec.check_out_url = False
