from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project.project'

    plan_id = fields.Many2one('account.analytic.plan')

    @api.model
    def create(self, vals):
        new_project = super(Project, self).create(vals)
        print(new_project, "new_project")
        if new_project:
            analytic_accounts = self.env['account.analytic.account'].search([('name', '=', new_project.name)])
            print(analytic_accounts, 'analytic_accounts')
            for account in analytic_accounts:
                account.write({'plan_id': new_project.plan_id.id})

        return new_project
