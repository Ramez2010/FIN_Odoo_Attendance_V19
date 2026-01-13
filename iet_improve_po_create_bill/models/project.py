from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = "project.project"

    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
    )
