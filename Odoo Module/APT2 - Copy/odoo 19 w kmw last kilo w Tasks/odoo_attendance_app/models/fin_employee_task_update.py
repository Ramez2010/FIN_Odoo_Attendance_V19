# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FinEmployeeTaskUpdate(models.Model):
    _name = 'fin.employee.task.update'
    _description = 'Employee Task Update'
    _order = 'updated_at desc, id desc'

    task_id = fields.Many2one(
        'fin.employee.task',
        string='Task',
        required=True,
        ondelete='cascade',
        index=True,
    )
    updated_at = fields.Datetime(
        string='Updated At',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    progress = fields.Integer(string='Progress (%)', required=True)
    update_note = fields.Text(string='Update Note')

    updated_by_employee_id = fields.Many2one(
        'hr.employee',
        string='Updated By (Employee)',
        ondelete='set null',
        index=True,
    )
    updated_by_user_id = fields.Many2one(
        'res.users',
        string='Updated By (User)',
        ondelete='set null',
        index=True,
    )

    @api.constrains('progress')
    def _check_progress_range(self):
        for rec in self:
            if rec.progress < 0 or rec.progress > 100:
                raise ValidationError('Progress must be between 0 and 100.')

