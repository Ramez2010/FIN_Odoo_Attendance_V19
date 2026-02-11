# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, fields
from odoo.osv import expression
from odoo.http import request
from odoo.exceptions import ValidationError
from .employee import authenticate_request
from .subscription import require_active_subscription
from ..utils import response_helper

_logger = logging.getLogger(__name__)


def _parse_date(raw, label):
    if raw in (None, ''):
        return None
    try:
        return fields.Date.to_date(raw)
    except Exception:
        raise ValidationError(f'{label} is invalid.')


def _parse_int(raw, label):
    if raw in (None, ''):
        return None
    try:
        return int(str(raw).strip())
    except Exception:
        raise ValidationError(f'{label} is invalid.')

def _parse_int_list(raw, label):
    if raw in (None, ''):
        return []
    if isinstance(raw, (list, tuple)):
        items = raw
    else:
        items = [raw]
    result = []
    for item in items:
        if item in (None, ''):
            continue
        try:
            result.append(int(str(item).strip()))
        except Exception:
            raise ValidationError(f'{label} is invalid.')
    return result


def _parse_float(raw, label):
    if raw in (None, ''):
        return None
    try:
        return float(str(raw).strip())
    except Exception:
        raise ValidationError(f'{label} must be a number.')


def _build_analytic_access_domain(hr_employee):
    return [
        ('active', '=', True),
        '|', ('x_allow_all_employees', '=', True),
             ('x_allowed_employee_ids', 'in', [hr_employee.id]),
    ]


def _serialize_task(task):
    assignees = task.assignee_ids
    if not assignees and task.employee_id:
        assignees = task.employee_id
    return {
        'id': task.id,
        'name': task.name or '',
        'description': task.description or '',
        'assignees': [
            {'id': emp.id, 'name': emp.name or ''}
            for emp in assignees
        ] if assignees else [],
        'employee': {
            'id': task.employee_id.id,
            'name': task.employee_id.name or '',
        } if task.employee_id else None,
        'manager': {
            'id': task.manager_id.id,
            'name': task.manager_id.name or '',
        } if task.manager_id else None,
        'analytic_account': {
            'id': task.analytic_account_id.id,
            'name': task.analytic_account_id.name or '',
            'code': task.analytic_account_id.code or '',
        } if task.analytic_account_id else None,
        'target_start_date': fields.Date.to_string(task.target_start_date)
        if task.target_start_date
        else None,
        'target_end_date': fields.Date.to_string(task.target_end_date)
        if task.target_end_date
        else None,
        'progress': int(task.progress or 0),
        'status': task.status or 'pending',
        'last_update_at': fields.Datetime.to_string(task.last_update_at)
        if task.last_update_at
        else None,
        'update_note': task.update_note or '',
        'priority': task.priority or '',
        'estimated_hours': task.estimated_hours or 0.0,
        'active': bool(task.active),
    }


class TasksController(http.Controller):
    """
    Employee task management endpoints.
    """

    def _get_fallback_employee_ids(self, hr_employee):
        EmployeeApp = request.env['odoo.attendance.employee'].sudo()
        app_records = EmployeeApp.search([('manager_employee_ids', 'in', [hr_employee.id])])
        return app_records.mapped('employee_id').ids

    def _get_manager_tree_employee_ids(self, hr_employee):
        """
        Resolve all indirect reports using the mobile app manager mapping.
        This walks the graph where each employee may have manager_employee_ids set.
        """
        EmployeeApp = request.env['odoo.attendance.employee'].sudo()
        seen_employee_ids = set()
        seen_manager_ids = {hr_employee.id}
        queue_manager_ids = {hr_employee.id}

        while queue_manager_ids:
            app_records = EmployeeApp.search([('manager_employee_ids', 'in', list(queue_manager_ids))])
            found_employee_ids = set(app_records.mapped('employee_id').ids)
            new_employee_ids = found_employee_ids - seen_employee_ids
            if not new_employee_ids:
                break
            seen_employee_ids.update(new_employee_ids)
            # Treat newly found employees as managers for next level
            new_manager_ids = new_employee_ids - seen_manager_ids
            if not new_manager_ids:
                break
            seen_manager_ids.update(new_manager_ids)
            queue_manager_ids = new_manager_ids

        return list(seen_employee_ids)

    def _get_team_employee_ids(self, hr_employee, include_self=False):
        Employee = request.env['hr.employee'].sudo()
        hierarchy_ids = Employee.search([('id', 'child_of', hr_employee.id)]).ids
        fallback_ids = self._get_manager_tree_employee_ids(hr_employee)
        ids = set(hierarchy_ids or [])
        ids.update(fallback_ids or [])
        if include_self:
            ids.add(hr_employee.id)
        else:
            ids.discard(hr_employee.id)
        return list(ids)

    @http.route('/api/odoo-attendance/tasks/assignees', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def list_task_assignees(self, **kwargs):
        """
        List employees under the current employee hierarchy (direct + indirect).
        Supports optional search query and pagination.
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            _employee_app, hr_employee = auth_result

            search_query = request.params.get('q', '').strip()
            limit = _parse_int(request.params.get('limit', 50), 'limit') or 50
            offset = _parse_int(request.params.get('offset', 0), 'offset') or 0
            include_self = str(request.params.get('include_self', '')).lower() in ('1', 'true', 'yes')

            domain = [('id', 'child_of', hr_employee.id), ('active', '=', True)]
            if not include_self:
                domain.append(('id', '!=', hr_employee.id))
            if search_query:
                domain.extend(['|', ('name', 'ilike', search_query), ('work_email', 'ilike', search_query)])

            Employee = request.env['hr.employee'].sudo()
            employees = Employee.search(domain, limit=limit, offset=offset, order='name asc')

            if not employees:
                # Fallback: use manager mapping from mobile app config if HR hierarchy isn't set.
                fallback_ids = self._get_manager_tree_employee_ids(hr_employee)
                if include_self and hr_employee.id not in fallback_ids:
                    fallback_ids.append(hr_employee.id)
                if fallback_ids:
                    fallback_domain = [('id', 'in', fallback_ids), ('active', '=', True)]
                    if search_query:
                        fallback_domain.extend(
                            ['|', ('name', 'ilike', search_query), ('work_email', 'ilike', search_query)]
                        )
                    employees = Employee.search(
                        fallback_domain,
                        limit=limit,
                        offset=offset,
                        order='name asc',
                    )

            results = []
            for emp in employees:
                results.append(
                    {
                        'id': emp.id,
                        'name': emp.name or '',
                        'job_title': emp.job_title or '',
                        'department': emp.department_id.name if emp.department_id else '',
                        'company': emp.company_id.name if emp.company_id else '',
                        'parent_id': emp.parent_id.id if emp.parent_id else None,
                        'has_children': bool(emp.child_ids),
                    }
                )

            return response_helper.success_response({'results': results})

        except ValidationError as e:
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in list_task_assignees endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

    @http.route('/api/odoo-attendance/my_tasks', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_my_tasks(self, **kwargs):
        """
        Returns tasks for the authenticated employee.

        Supports filters similar to the team_tasks endpoint:
        - analytic_account_id
        - status: pending | in_process | done
        - date_from / date_to (overlap with task target dates)
        - limit / offset

        Backward compatibility:
        - If `date` is provided (legacy clients), it's treated as date_from=date_to=date.
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            _employee_app, hr_employee = auth_result

            legacy_date = _parse_date(request.params.get('date'), 'date')
            date_from = _parse_date(request.params.get('date_from'), 'date_from')
            date_to = _parse_date(request.params.get('date_to'), 'date_to')
            if legacy_date and not date_from and not date_to:
                date_from = legacy_date
                date_to = legacy_date

            analytic_account_id = _parse_int(request.params.get('analytic_account_id'), 'analytic_account_id')
            status = (request.params.get('status') or '').strip()
            task_id = _parse_int(request.params.get('task_id'), 'task_id')

            Task = request.env['fin.employee.task'].sudo()
            domain = [
                ('active', '=', True),
                '|',
                ('assignee_ids', 'in', [hr_employee.id]),
                ('employee_id', '=', hr_employee.id),
            ]

            if analytic_account_id:
                domain.append(('analytic_account_id', '=', analytic_account_id))

            if status:
                if status not in ('pending', 'in_process', 'done'):
                    return response_helper.validation_error_response('Invalid status filter.')
                domain.append(('status', '=', status))

            if date_from and date_to:
                domain.extend([
                    ('target_start_date', '<=', date_to),
                    ('target_end_date', '>=', date_from),
                ])
            elif date_from:
                domain.append(('target_end_date', '>=', date_from))
            elif date_to:
                domain.append(('target_start_date', '<=', date_to))

            if task_id:
                domain.append(('id', '=', task_id))

            limit = _parse_int(request.params.get('limit'), 'limit')
            offset = _parse_int(request.params.get('offset'), 'offset') or 0
            if limit is not None:
                limit = max(1, min(limit, 200))
            else:
                # Legacy behavior: if a client requests a single day without pagination params, return all items.
                limit = None if legacy_date else 50
            offset = max(0, offset)

            tasks = Task.search(
                domain,
                limit=limit,
                offset=offset,
                order='target_end_date asc, progress asc, id desc',
            )
            results = [_serialize_task(task) for task in tasks]

            return response_helper.success_response({'items': results})

        except ValidationError as e:
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in get_my_tasks endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

    @http.route('/api/odoo-attendance/team_tasks', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_team_tasks(self, **kwargs):
        """
        Returns tasks assigned by the manager or within their hierarchy (including self).
        Supports filtering and optional summary metrics.
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            _employee_app, hr_employee = auth_result

            employee_id = _parse_int(request.params.get('employee_id'), 'employee_id')
            analytic_account_id = _parse_int(request.params.get('analytic_account_id'), 'analytic_account_id')
            status = (request.params.get('status') or '').strip()
            date_from = _parse_date(request.params.get('date_from'), 'date_from')
            date_to = _parse_date(request.params.get('date_to'), 'date_to')
            task_id = _parse_int(request.params.get('task_id'), 'task_id')
            limit = _parse_int(request.params.get('limit', 50), 'limit') or 50
            offset = _parse_int(request.params.get('offset', 0), 'offset') or 0
            include_summary = str(request.params.get('include_summary', '1')).lower() in ('1', 'true', 'yes')

            Task = request.env['fin.employee.task'].sudo()
            team_employee_ids = self._get_team_employee_ids(hr_employee, include_self=False)
            base_domain = [
                ('active', '=', True),
                '|',
                ('assignee_ids', 'in', team_employee_ids or [0]),
                ('employee_id', 'in', team_employee_ids or [0]),
            ]

            if employee_id:
                if employee_id not in team_employee_ids:
                    return response_helper.forbidden_response('Employee is not in your hierarchy.')
                base_domain.extend([
                    '|',
                    ('assignee_ids', 'in', [employee_id]),
                    ('employee_id', '=', employee_id),
                ])

            if analytic_account_id:
                base_domain.append(('analytic_account_id', '=', analytic_account_id))

            if status:
                if status not in ('pending', 'in_process', 'done'):
                    return response_helper.validation_error_response('Invalid status filter.')
                base_domain.append(('status', '=', status))

            if date_from and date_to:
                base_domain.extend([
                    ('target_start_date', '<=', date_to),
                    ('target_end_date', '>=', date_from),
                ])
            elif date_from:
                base_domain.append(('target_end_date', '>=', date_from))
            elif date_to:
                base_domain.append(('target_start_date', '<=', date_to))

            if task_id:
                base_domain.append(('id', '=', task_id))

            tasks = Task.search(
                base_domain,
                limit=limit,
                offset=offset,
                order='target_end_date asc, progress asc, id desc',
            )
            results = [_serialize_task(task) for task in tasks]

            payload = {'items': results}

            if include_summary:
                payload['summary'] = self._build_team_summary(Task, base_domain)

            return response_helper.success_response(payload)

        except ValidationError as e:
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in get_team_tasks endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

    def _build_team_summary(self, Task, domain):
        tasks_count = Task.search_count(domain)
        summary = {
            'counts_by_status': {'pending': 0, 'in_process': 0, 'done': 0},
            'avg_progress_by_employee': [],
            'avg_progress_by_analytic': [],
        }

        if not tasks_count:
            return summary

        status_groups = Task.read_group(domain, ['status'], ['status'], lazy=False)
        for group in status_groups:
            status = group.get('status')
            count = group.get('__count', 0)
            if status in summary['counts_by_status']:
                summary['counts_by_status'][status] = count

        # Fallback for counts if grouping didn't return expected buckets
        if sum(summary['counts_by_status'].values()) == 0 and tasks_count > 0:
            pending_domain = expression.AND([domain, [('progress', '=', 0)]])
            in_process_domain = expression.AND([domain, [('progress', '>', 0), ('progress', '<', 100)]])
            done_domain = expression.AND([domain, [('progress', '>=', 100)]])
            summary['counts_by_status']['pending'] = Task.search_count(pending_domain)
            summary['counts_by_status']['in_process'] = Task.search_count(in_process_domain)
            summary['counts_by_status']['done'] = Task.search_count(done_domain)

        emp_groups = Task.read_group(domain, ['progress:avg'], ['assignee_ids'], lazy=False)
        if not emp_groups:
            emp_groups = Task.read_group(domain, ['progress:avg'], ['employee_id'], lazy=False)

        for group in emp_groups:
            emp = group.get('assignee_ids') or group.get('employee_id')
            avg = group.get('progress_avg')
            if avg is None:
                avg = group.get('progress')
            if emp:
                summary['avg_progress_by_employee'].append(
                    {
                        'employee_id': emp[0],
                        'employee_name': emp[1],
                        'avg_progress': round(avg or 0.0, 1),
                    }
                )

        analytic_groups = Task.read_group(domain, ['progress:avg'], ['analytic_account_id'], lazy=False)
        for group in analytic_groups:
            analytic = group.get('analytic_account_id')
            avg = group.get('progress_avg')
            if avg is None:
                avg = group.get('progress')
            if analytic:
                summary['avg_progress_by_analytic'].append(
                    {
                        'analytic_account_id': analytic[0],
                        'analytic_account_name': analytic[1],
                        'avg_progress': round(avg or 0.0, 1),
                    }
                )

        summary['avg_progress_by_employee'].sort(key=lambda x: x['employee_name'])
        summary['avg_progress_by_analytic'].sort(key=lambda x: x['analytic_account_name'])
        return summary

    @http.route('/api/odoo-attendance/tasks', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_task(self, **kwargs):
        """
        Create a new task (manager only). Employee must be within hierarchy.
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            _employee_app, hr_employee = auth_result

            try:
                data = json.loads(request.httprequest.data)
            except Exception:
                return response_helper.validation_error_response('Invalid JSON in request body')

            name = (data.get('name') or '').strip()
            description = (data.get('description') or '').strip()
            employee_ids = _parse_int_list(data.get('employee_ids'), 'employee_ids')
            employee_id = _parse_int(data.get('employee_id'), 'employee_id')
            analytic_account_id = _parse_int(data.get('analytic_account_id'), 'analytic_account_id')
            target_start_date = _parse_date(data.get('target_start_date'), 'target_start_date')
            target_end_date = _parse_date(data.get('target_end_date'), 'target_end_date')
            priority = (data.get('priority') or '').strip() or False
            estimated_hours = _parse_float(data.get('estimated_hours'), 'estimated_hours')
            allow_self_raw = data.get('allow_self')
            allow_self = str(allow_self_raw).lower() in ('1', 'true', 'yes')

            if not name:
                return response_helper.validation_error_response('Task title is required.')
            if not employee_ids and employee_id:
                employee_ids = [employee_id]
            if not employee_ids:
                return response_helper.validation_error_response('employee_ids is required.')
            if not analytic_account_id:
                return response_helper.validation_error_response('analytic_account_id is required.')
            if not target_start_date or not target_end_date:
                return response_helper.validation_error_response('Target start and end dates are required.')
            if target_end_date < target_start_date:
                return response_helper.validation_error_response('End date must be on or after start date.')
            if priority and priority not in ('low', 'medium', 'high'):
                return response_helper.validation_error_response('Invalid priority value.')

            Employee = request.env['hr.employee'].sudo()
            assignees = Employee.browse(employee_ids).exists()
            if not assignees or len(assignees) != len(set(employee_ids)):
                return response_helper.validation_error_response('Employee not found.')

            if not allow_self and hr_employee.id in assignees.ids:
                return response_helper.forbidden_response('Cannot assign a task to yourself.')

            allowed_ids = set(self._get_team_employee_ids(hr_employee, include_self=allow_self))
            for emp in assignees:
                if emp.id not in allowed_ids:
                    return response_helper.forbidden_response('Employee is not in your hierarchy.')

            Analytic = request.env['account.analytic.account'].sudo()
            for emp in assignees:
                analytic_domain = [('id', '=', analytic_account_id)] + _build_analytic_access_domain(emp)
                analytic = Analytic.search(analytic_domain, limit=1)
                if not analytic:
                    return response_helper.forbidden_response(
                        'Analytic account is not accessible to the employee.'
                    )

            Task = request.env['fin.employee.task'].sudo()
            primary_id = assignees[0].id if assignees else employee_ids[0]
            task = Task.create(
                {
                    'name': name,
                    'description': description,
                    'employee_id': primary_id,
                    'assignee_ids': [(6, 0, assignees.ids)],
                    'manager_id': hr_employee.id,
                    'analytic_account_id': analytic.id,
                    'target_start_date': target_start_date,
                    'target_end_date': target_end_date,
                    'priority': priority or False,
                    'estimated_hours': estimated_hours,
                }
            )

            return response_helper.success_response({'task': _serialize_task(task)})

        except ValidationError as e:
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in create_task endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

    @http.route('/api/odoo-attendance/tasks/<int:task_id>/progress', type='http', auth='public', methods=['PATCH', 'POST'], csrf=False, cors='*')
    def update_task_progress(self, task_id, **kwargs):
        """
        Update progress for an employee's own task.
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            _employee_app, hr_employee = auth_result

            try:
                data = json.loads(request.httprequest.data)
            except Exception:
                return response_helper.validation_error_response('Invalid JSON in request body')

            progress = _parse_int(data.get('progress'), 'progress')
            update_note = data.get('update_note', None)

            if progress is None:
                return response_helper.validation_error_response('progress is required.')
            if progress < 0 or progress > 100:
                return response_helper.validation_error_response('progress must be between 0 and 100.')

            Task = request.env['fin.employee.task'].sudo()
            task = Task.browse(task_id)
            if not task.exists():
                return response_helper.not_found_response('Task not found.')

            assignee_ids = task.assignee_ids.ids or []
            if hr_employee.id not in assignee_ids and task.employee_id.id != hr_employee.id:
                return response_helper.forbidden_response('You can only update your own tasks.')

            vals = {
                'progress': progress,
                'last_update_at': fields.Datetime.now(),
            }
            if update_note is not None:
                vals['update_note'] = (update_note or '').strip()
            ctx = {'task_update_actor_employee_id': hr_employee.id}
            if getattr(hr_employee, 'user_id', False) and hr_employee.user_id:
                ctx['task_update_actor_user_id'] = hr_employee.user_id.id
            task.with_context(**ctx).write(vals)

            return response_helper.success_response({'task': _serialize_task(task)})

        except ValidationError as e:
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in update_task_progress endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

    @http.route('/api/odoo-attendance/tasks/<int:task_id>/delegate', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def delegate_task(self, task_id, **kwargs):
        """
        Delegate a task from the authenticated employee to a subordinate.
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            _employee_app, hr_employee = auth_result

            try:
                data = json.loads(request.httprequest.data)
            except Exception:
                return response_helper.validation_error_response('Invalid JSON in request body')

            target_employee_id = _parse_int(data.get('employee_id'), 'employee_id')
            if not target_employee_id:
                return response_helper.validation_error_response('employee_id is required.')

            Task = request.env['fin.employee.task'].sudo()
            task = Task.browse(task_id)
            if not task.exists():
                return response_helper.not_found_response('Task not found.')

            current_assignees = set(task.assignee_ids.ids or [])
            if not current_assignees and task.employee_id:
                current_assignees.add(task.employee_id.id)

            if hr_employee.id not in current_assignees and task.employee_id.id != hr_employee.id:
                return response_helper.forbidden_response('You can only delegate your own tasks.')

            allowed_ids = set(self._get_team_employee_ids(hr_employee, include_self=False))
            if target_employee_id not in allowed_ids:
                return response_helper.forbidden_response('Employee is not in your hierarchy.')

            current_assignees.add(hr_employee.id)
            current_assignees.add(target_employee_id)

            vals = {
                'assignee_ids': [(6, 0, list(current_assignees))],
            }
            if task.employee_id and task.employee_id.id == hr_employee.id:
                vals['employee_id'] = target_employee_id

            task.write(vals)

            return response_helper.success_response({'task': _serialize_task(task)})

        except ValidationError as e:
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in delegate_task endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')
