# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request
from .employee import authenticate_request
from ..utils import response_helper
from .subscription import require_active_subscription

_logger = logging.getLogger(__name__)


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
            limit = int(request.params.get('limit', 20))
            
            # Search analytic accounts
            AnalyticAccount = request.env['account.analytic.account'].sudo()

            # Visible if allow-all, or employee explicitly allowed
            domain = [
                ('active', '=', True),
                '|', ('x_allow_all_employees', '=', True),
                     ('x_allowed_employee_ids', 'in', [hr_employee.id]),
            ]
            
            # Add search filter if query provided
            if search_query:
                domain.append('|')
                domain.append(('name', 'ilike', search_query))
                domain.append(('code', 'ilike', search_query))
            
            accounts = AnalyticAccount.search(domain, limit=limit, order='name')
            
            results = []
            for account in accounts:
                results.append({
                    'id': account.id,
                    'name': account.name,
                    'code': account.code or '',
                })
            
            return response_helper.success_response(results)
            
        except Exception as e:
            _logger.exception(f'Error in search_analytics endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')
