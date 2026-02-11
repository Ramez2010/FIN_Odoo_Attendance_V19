# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FinEmployeeTask(models.Model):
    _name = 'fin.employee.task'
    _description = 'Employee Task'
    _order = 'target_start_date desc, id desc'

    name = fields.Char(string='Title', required=True, index=True)
    description = fields.Text(string='Description')
    employee_id = fields.Many2one(
        'hr.employee',
        string='Primary Employee',
        required=True,
        index=True,
        ondelete='restrict',
    )
    assignee_ids = fields.Many2many(
        'hr.employee',
        'fin_employee_task_assignee_rel',
        'task_id',
        'employee_id',
        string='Assignees',
        help='Employees assigned to this task (shared progress).',
    )
    manager_id = fields.Many2one(
        'hr.employee',
        string='Assigned By',
        required=True,
        index=True,
        ondelete='restrict',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        required=True,
        index=True,
        ondelete='restrict',
    )
    target_start_date = fields.Date(string='Target Start Date', required=True, index=True)
    target_end_date = fields.Date(string='Target End Date', required=True, index=True)
    progress = fields.Integer(string='Progress (%)', default=0)
    progress_avg = fields.Float(
        string='Progress (%)',
        compute='_compute_progress_avg',
        store=True,
        group_operator='avg',
    )
    progress_target = fields.Integer(
        string='Progress Target',
        compute='_compute_progress_target',
        store=True,
    )
    status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('in_process', 'In Process'),
            ('done', 'Done'),
        ],
        string='Status',
        compute='_compute_status',
        store=True,
        index=True,
    )
    last_update_at = fields.Datetime(
        string='Last Update At',
        default=fields.Datetime.now,
        index=True,
    )
    update_note = fields.Text(string='Update Note')
    update_history_ids = fields.One2many(
        'fin.employee.task.update',
        'task_id',
        string='Update History',
        readonly=True,
        copy=False,
    )
    priority = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        string='Priority',
    )
    estimated_hours = fields.Float(string='Estimated Hours')
    active = fields.Boolean(default=True)

    @api.depends('progress')
    def _compute_status(self):
        for task in self:
            progress = task.progress or 0
            if progress <= 0:
                task.status = 'pending'
            elif progress < 100:
                task.status = 'in_process'
            else:
                task.status = 'done'

    @api.depends('progress')
    def _compute_progress_avg(self):
        for task in self:
            task.progress_avg = float(task.progress or 0)

    @api.depends('progress')
    def _compute_progress_target(self):
        for task in self:
            task.progress_target = 100

    @api.constrains('progress')
    def _check_progress_range(self):
        for task in self:
            if task.progress is None:
                continue
            if task.progress < 0 or task.progress > 100:
                raise ValidationError('Progress must be between 0 and 100.')

    @api.constrains('target_start_date', 'target_end_date')
    def _check_dates(self):
        for task in self:
            if task.target_start_date and task.target_end_date:
                if task.target_end_date < task.target_start_date:
                    raise ValidationError('Target End Date must be on or after Target Start Date.')

    @staticmethod
    def _extract_assignee_ids(value, current_ids):
        if value is None:
            return list(current_ids or [])
        if isinstance(value, (list, tuple)):
            if not value:
                return []
            # List of ints -> direct ids
            if isinstance(value[0], int):
                return list(dict.fromkeys(int(v) for v in value))
            # M2M commands
            ids = set(current_ids or [])
            for cmd in value:
                if not isinstance(cmd, (list, tuple)) or not cmd:
                    continue
                command = cmd[0]
                if command == 6:
                    ids = set(cmd[2] or [])
                elif command == 4:
                    ids.add(cmd[1])
                elif command == 3:
                    ids.discard(cmd[1])
                elif command == 5:
                    ids.clear()
            return list(ids)
        return list(current_ids or [])

    def _normalize_assignees_vals(self, vals, current_assignee_ids=None):
        current_assignee_ids = current_assignee_ids or []
        employee_id = vals.get('employee_id') or (self.employee_id.id if self else None)
        assignee_val = vals.get('assignee_ids', None)

        if assignee_val is None:
            if employee_id:
                vals['assignee_ids'] = [(6, 0, [employee_id])]
            return vals

        ids = self._extract_assignee_ids(assignee_val, current_assignee_ids)
        if not ids and employee_id:
            ids = [employee_id]
        if employee_id and employee_id not in ids:
            ids.append(employee_id)
        if not employee_id and ids:
            vals['employee_id'] = ids[0]
        vals['assignee_ids'] = [(6, 0, ids)]
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        normalized = []
        for vals in vals_list:
            vals = dict(vals or {})
            vals = self._normalize_assignees_vals(vals, [])
            normalized.append(vals)
        return super(FinEmployeeTask, self).create(normalized)

    def _create_update_history_entries(self, *, write_vals=None):
        """
        Append one history line per task capturing the latest progress + note.

        Uses context keys set by API controllers when running under sudo:
        - task_update_actor_employee_id
        - task_update_actor_user_id
        """
        Update = self.env['fin.employee.task.update'].sudo()
        actor_employee_id = self.env.context.get('task_update_actor_employee_id')
        actor_user_id = self.env.context.get('task_update_actor_user_id') or self.env.user.id
        write_vals = dict(write_vals or {})

        vals_list = []
        for task in self:
            updated_at = write_vals.get('last_update_at') or task.last_update_at or fields.Datetime.now()
            vals_list.append(
                {
                    'task_id': task.id,
                    'updated_at': updated_at,
                    'progress': int(task.progress or 0),
                    'update_note': task.update_note or '',
                    'updated_by_employee_id': actor_employee_id or False,
                    'updated_by_user_id': actor_user_id or False,
                }
            )
        if vals_list:
            Update.create(vals_list)

    def write(self, vals):
        vals = dict(vals or {})
        wants_log = (
            ('progress' in vals or 'update_note' in vals)
            and not self.env.context.get('skip_task_update_log')
        )

        if 'progress' in vals or 'update_note' in vals:
            vals.setdefault('last_update_at', fields.Datetime.now())

        if 'assignee_ids' in vals or 'employee_id' in vals:
            for record in self:
                record_vals = dict(vals)
                record_vals = record._normalize_assignees_vals(
                    record_vals,
                    record.assignee_ids.ids,
                )
                should_log = False
                if wants_log:
                    old_progress = int(record.progress or 0)
                    old_note = record.update_note or ''
                    new_progress = int(record_vals.get('progress', old_progress) or 0)
                    if 'update_note' in record_vals:
                        new_note = record_vals.get('update_note') or ''
                    else:
                        new_note = old_note
                    should_log = (new_progress != old_progress) or (
                        'update_note' in record_vals and new_note != old_note
                    )
                super(FinEmployeeTask, record).write(record_vals)
                if should_log:
                    record._create_update_history_entries(write_vals=record_vals)
            return True

        to_log = self.browse()
        if wants_log:
            for record in self:
                old_progress = int(record.progress or 0)
                old_note = record.update_note or ''
                new_progress = int(vals.get('progress', old_progress) or 0)
                if 'update_note' in vals:
                    new_note = vals.get('update_note') or ''
                else:
                    new_note = old_note
                if (new_progress != old_progress) or (
                    'update_note' in vals and new_note != old_note
                ):
                    to_log |= record

        res = super(FinEmployeeTask, self).write(vals)
        if to_log:
            to_log._create_update_history_entries(write_vals=vals)
        return res

    @api.model
    def init(self):
        """Ensure existing tasks have assignees populated from the primary employee."""
        self.env.cr.execute(
            """
            INSERT INTO fin_employee_task_assignee_rel (task_id, employee_id)
            SELECT t.id, t.employee_id
            FROM fin_employee_task t
            WHERE t.employee_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM fin_employee_task_assignee_rel rel
                WHERE rel.task_id = t.id
              )
            """
        )
        self.env.cr.execute(
            """
            UPDATE fin_employee_task
               SET status = CASE
                   WHEN COALESCE(progress, 0) <= 0 THEN 'pending'
                   WHEN COALESCE(progress, 0) < 100 THEN 'in_process'
                   ELSE 'done'
               END
             WHERE status IS NULL
            """
        )
