from odoo import fields, models, api, _


class HrLeave(models.Model):
    _inherit = "hr.leave"

    is_updated = fields.Boolean('Is Updated')