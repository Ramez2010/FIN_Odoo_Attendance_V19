# -*- coding: utf-8 -*-
import json
import logging
from odoo import http, fields
from odoo.http import request
from ..utils import jwt_helper, response_helper
from .subscription import require_active_subscription

_logger = logging.getLogger(__name__)


def authenticate_request():
    """
    Middleware to authenticate API requests using JWT.
    Extracts and verifies access token from Authorization header.
    
    Returns: tuple (employee_app_record, hr_employee_record) or None
    """
    auth_header = request.httprequest.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    token = jwt_helper.extract_bearer_token(auth_header)
    if not token:
        return None
    
    try:
        payload = jwt_helper.verify_token(request.env, token, expected_type='access')
        employee_app_id = int(payload['sub'])
        
        # Disable prefetch to avoid selecting newly-added columns before module upgrade
        EmployeeApp = request.env['odoo.attendance.employee'].sudo().with_context(prefetch_fields=False)
        employee_app = EmployeeApp.browse(employee_app_id)
        
        if not employee_app.exists() or not employee_app.is_active:
            return None
        
        return employee_app, employee_app.employee_id
        
    except Exception as e:
        _logger.warning(f'Authentication failed: {str(e)}')
        return None


class EmployeeController(http.Controller):
    """
    Employee profile and location endpoints.
    """
    
    @http.route('/api/odoo-attendance/employee/profile', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_profile(self, **kwargs):
        """
        Get employee profile and current attendance status.
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
            
            # Get current attendance status
            Attendance = request.env['hr.attendance'].sudo()
            current_attendance = Attendance.search([
                ('employee_id', '=', hr_employee.id),
                ('check_out', '=', False)
            ], limit=1)
            
            attendance_data = None
            if current_attendance:
                attendance_data = {
                    'id': current_attendance.id,
                    'check_in': current_attendance.check_in.isoformat() if current_attendance.check_in else None,
                    'analytic_account': {
                        'id': current_attendance.x_analytic_account_id.id,
                        'name': current_attendance.x_analytic_account_id.name
                    } if current_attendance.x_analytic_account_id else None,
                    'worked_hours': current_attendance.worked_hours
                }
            
            return response_helper.success_response({
                'employee': {
                    'id': hr_employee.id,
                    'name': hr_employee.name,
                    'username': employee_app.username,
                    'email': hr_employee.work_email or '',
                    'job_title': hr_employee.job_title or '',
                    'department': hr_employee.department_id.name if hr_employee.department_id else '',
                    'company': hr_employee.company_id.name if hr_employee.company_id else ''
                },
                'attendance_status': {
                    'is_checked_in': bool(current_attendance),
                    'current_attendance': attendance_data
                }
            })
            
        except Exception as e:
            _logger.exception(f'Error in get_profile endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

    @http.route('/api/odoo-attendance/employee/update-location', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def update_live_location(self, **kwargs):
        """
        Receives a location update from the mobile app in response to a request.
        """
        try:
            # Authenticate
            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')
            
            _employee_app, hr_employee = auth_result

            # Parse request body
            try:
                data = json.loads(request.httprequest.data)
            except:
                return response_helper.validation_error_response('Invalid JSON')

            gps_lat = data.get('gps_lat')
            gps_lng = data.get('gps_lng')
            gps_accuracy = data.get('gps_accuracy')

            if not all([gps_lat, gps_lng]):
                return response_helper.validation_error_response('gps_lat and gps_lng are required')

            # Find existing record to update or create a new one
            LiveLocation = request.env['employee.live.location'].sudo()
            location_record = LiveLocation.search([('employee_id', '=', hr_employee.id)], limit=1)

            location_vals = {
                'employee_id': hr_employee.id,
                'gps_lat': gps_lat,
                'gps_lng': gps_lng,
                'gps_accuracy': gps_accuracy,
                'located_at': fields.Datetime.now(),
                'status': 'received',
            }

            if location_record:
                location_record.write(location_vals)
            else:
                LiveLocation.create(location_vals)

            return response_helper.success_response({'status': 'ok'})

        except Exception as e:
            _logger.exception(f'Error in update_live_location endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')
