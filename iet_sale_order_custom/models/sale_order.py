from odoo import api, fields, models
from odoo.exceptions import ValidationError

READONLY_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'sale', 'done', 'cancel'}
}

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    display_project_id = fields.Many2one('project.project', index=True, string='Project')
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Analytic Account",
        copy=False, check_company=True,  # Unrequired company
        compute='_compute_analytic_account_id',
        store=True,)

    employee = fields.Many2one('hr.employee')
    def action_confirm(self):
        if not self.analytic_account_id:
            raise ValidationError("The Analytic Account Field Must Be Set")
        else:
            return super(SaleOrder, self).action_confirm()

    @api.depends('display_project_id')
    def _compute_analytic_account_id(self):
        for rec in self:
            if rec.display_project_id:
                print("5")
                rec.analytic_account_id = rec.display_project_id.analytic_account_id

    def sale_project_update(self):
        orders = self.search([])
        for order in orders:
            if order.analytic_account_id and not order.display_project_id:
                project_id = self.env['project.project'].search(
                    [('analytic_account_id', '=', order.analytic_account_id.id)], limit=1)
                if project_id:
                    order.display_project_id = project_id
