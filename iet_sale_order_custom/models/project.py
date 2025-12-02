from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project.project'

    plan_id = fields.Many2one('account.analytic.plan', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        new_projects = super(Project, self).create(vals_list)
        for project in new_projects:
            if project.name and project.plan_id:
                analytic_accounts = self.env['account.analytic.account'].search([('name', '=', project.name)])
                if analytic_accounts:
                    analytic_accounts.write({'plan_id': project.plan_id.id})
        return new_projects
