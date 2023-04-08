from odoo import _, api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Hr Contract'

    meal_allowance = fields.Float(string='Meal Allowance')
    mobil_allowance = fields.Float(string='Mobil Allowance')
    transportation_allowance = fields.Float(string='Transportation Allowance')
    car_allowance = fields.Float(string='Car Allowance')
