from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def create(self, vals):
        # If a user is being assigned during creation, check the limit
        if vals.get('user_id'):
            self._check_user_limit()

        return super(HREmployee, self).create(vals)

    def write(self, vals):
        # Check if an employee is being unarchived
        if 'active' in vals and vals['active']:
            # Check if the employee has an assigned user and enforce the limit
            for employee in self:
                if employee.user_id:
                    self._check_user_limit()

        # If a user is being assigned, enforce the limit
        if 'user_id' in vals and vals['user_id']:
            self._check_user_limit()

        return super(HREmployee, self).write(vals)

    @api.model
    def _check_user_limit(self):
        # Count employees linked to active users
        employee_with_active_users_count = self.env['hr.employee'].search_count([
            ('user_id.active', '=', True)
        ])

        max_users = 50  # Adjust this value

        if employee_with_active_users_count >= max_users:
            raise UserError(_("You cannot assign more users to employees. The maximum limit of %s active users has been reached.\n Please contact your RiadaHR Customer Support (support@alriada.tech) to purchase more users.") % max_users)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def write(self, vals):
        # Check if the user is being reactivated
        if 'active' in vals and vals['active']:
            # Find employees linked to the users being reactivated
            linked_employees = self.env['hr.employee'].search([('user_id', 'in', self.ids)])

            # If any employee is linked to the reactivated user, enforce the limit
            if linked_employees:
                linked_employees._check_user_limit()

        return super(ResUsers, self).write(vals)
