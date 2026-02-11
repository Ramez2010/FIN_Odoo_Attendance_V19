# -*- coding: utf-8 -*-
import json
from odoo.http import Response


def json_response(data, status=200):
    """
    Create JSON response for REST API.
    
    Args:
        data: Dictionary or list to return as JSON
        status: HTTP status code (default 200)
    
    Returns:
        Odoo Response object with JSON content
    """
    return Response(
        json.dumps(data, default=str, ensure_ascii=False),
        status=status,
        content_type='application/json; charset=utf-8'
    )


def success_response(data=None, message=None):
    """
    Create success response (HTTP 200).
    
    Format:
    {
        "success": true,
        "data": {...},
        "message": "..."
    }
    """
    response_data = {'success': True}
    
    if data is not None:
        response_data['data'] = data
    
    if message:
        response_data['message'] = message
    
    return json_response(response_data, status=200)


def error_response(message, status=400, error_code=None):
    """
    Create error response.
    
    Format:
    {
        "success": false,
        "error": "Error message",
        "error_code": "SPECIFIC_ERROR_CODE"
    }
    """
    response_data = {
        'success': False,
        'error': message
    }
    
    if error_code:
        response_data['error_code'] = error_code
    
    return json_response(response_data, status=status)


def unauthorized_response(message='Unauthorized'):
    """Create 401 Unauthorized response"""
    return error_response(message, status=401, error_code='UNAUTHORIZED')


def forbidden_response(message='Forbidden'):
    """Create 403 Forbidden response"""
    return error_response(message, status=403, error_code='FORBIDDEN')


def not_found_response(message='Not found'):
    """Create 404 Not Found response"""
    return error_response(message, status=404, error_code='NOT_FOUND')


def validation_error_response(message):
    """Create 422 Validation Error response"""
    return error_response(message, status=422, error_code='VALIDATION_ERROR')


def payment_required_response(message='Subscription required'):
    """Create 402 Payment Required response"""
    return error_response(message, status=402, error_code='PAYMENT_REQUIRED')


def server_error_response(message='Internal server error'):
    """Create 500 Server Error response"""
    return error_response(message, status=500, error_code='SERVER_ERROR')
