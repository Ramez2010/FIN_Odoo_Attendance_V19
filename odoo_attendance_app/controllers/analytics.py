# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request
from .employee import authenticate_request
from ..utils import response_helper
from .subscription import require_active_subscription

_logger = logging.getLogger(__name__)


def _get_mobile_project_source(env):
    """
    Read the configured mobile project source (projects, analytic accounts, or sale order field).
    """
    return (
        env['ir.config_parameter']
        .sudo()
        .get_param('odoo_attendance_app.mobile_project_source', default='analytic_account')
        or 'analytic_account'
    )


def _build_analytic_access_domain(hr_employee):
    return [
        ('active', '=', True),
        '|', ('x_allow_all_employees', '=', True),
             ('x_allowed_employee_ids', 'in', [hr_employee.id]),
    ]


def _search_analytic_accounts(env, hr_employee, search_query, limit):
    AnalyticAccount = env['account.analytic.account'].sudo()
    domain = _build_analytic_access_domain(hr_employee)
    if search_query:
        domain.extend(['|', ('name', 'ilike', search_query), ('code', 'ilike', search_query)])
    accounts = AnalyticAccount.search(domain, limit=limit or False, order='name')
    return [
        {
            'id': account.id,
            'name': f'[{(account.code or str(account.id)).strip()}] {account.name}'
            if account.name
            else f'[{(account.code or str(account.id)).strip()}]',
            'code': account.code or '',
            'source': 'analytic_account',
        }
        for account in accounts
    ]


def _search_projects(env, hr_employee, search_query, limit):
    Project = env['project.project'].sudo()
    domain = [
        ('active', '=', True),
        ('analytic_account_id', '!=', False),
        ('analytic_account_id.active', '=', True),
        '|', ('analytic_account_id.x_allow_all_employees', '=', True),
             ('analytic_account_id.x_allowed_employee_ids', 'in', [hr_employee.id]),
    ]
    if search_query:
        domain.extend(['|', ('name', 'ilike', search_query), ('analytic_account_id.name', 'ilike', search_query)])
    projects = Project.search(domain, limit=limit or False, order='name')
    seen = set()
    results = []
    for project in projects:
        analytic = project.analytic_account_id
        if not analytic or analytic.id in seen:
            continue
        seen.add(analytic.id)
        code = analytic.code or getattr(project, 'code', '') or ''
        display_code = (analytic.code or str(analytic.id)).strip()
        title = project.name or analytic.name or ''
        label = f'[{display_code}] {title}' if title else f'[{display_code}]'
        results.append({
            'id': analytic.id,
            'name': label,
            'code': code,
            'source': 'projects',
            'project_id': project.id,
            'project_name': project.name,
            'analytic_account_name': analytic.name,
        })
    return results


class AnalyticsController(http.Controller):
    """
    Analytic account search endpoints.
    """
    
    @http.route('/api/odoo-attendance/analytics/search', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def search_analytics(self, **kwargs):
        """
        Search analytic accounts filtered by employee access.
        
        GET /api/odoo-attendance/analytics/search?q=project&limit=20
        Authorization: Bearer <access_token>
        
        Query parameters:
        - q: search query (optional)
        - limit: max results (default 20)
        
        Response:
        {
            "success": true,
            "data": [
                {"id": 1, "name": "Project Alpha", "code": "PA001"},
                ...
            ]
        }
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            # Authenticate
            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')
            
            employee_app, hr_employee = auth_result
            
            # Get query parameters
            search_query = request.params.get('q', '').strip()
            limit = int(request.params.get('limit', 0))
            
            # Search analytic accounts
            project_source = _get_mobile_project_source(request.env)
            if project_source == 'projects':
                results = _search_projects(request.env, hr_employee, search_query, limit)
            else:
                results = _search_analytic_accounts(request.env, hr_employee, search_query, limit)

            return response_helper.success_response(results)

        except Exception as e:
            _logger.exception(f'Error in search_analytics endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

