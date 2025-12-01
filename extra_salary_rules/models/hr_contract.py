from odoo import _, api, fields, models


class HrVersion(models.Model):
    _inherit = 'hr.version'
    _description = 'Hr Version Inherit'

    meal_allowance = fields.Float(string='Meal Allowance')
    mobil_allowance = fields.Float(string='Mobil Allowance')
    transportation_allowance = fields.Float(string='Transportation Allowance')
    car_allowance = fields.Float(string='Car Allowance')