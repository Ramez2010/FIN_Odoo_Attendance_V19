from odoo import models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    is_worker = fields.Boolean(string="Is worker?")
