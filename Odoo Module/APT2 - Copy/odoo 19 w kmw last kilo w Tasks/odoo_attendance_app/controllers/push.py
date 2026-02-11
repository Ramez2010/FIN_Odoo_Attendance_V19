# -*- coding: utf-8 -*-
import json
import logging

from odoo import http, fields
from odoo.http import request

from .employee import authenticate_request
from ..utils import response_helper
from .subscription import require_active_subscription


_logger = logging.getLogger(__name__)


class PushController(http.Controller):
    """
    Push notification registration endpoints (Android-only via FCM).
    """

    @http.route('/api/odoo-attendance/push/register', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def register_push_token(self, **kwargs):
        """
        Register (or update) the device push token for the authenticated Mobile App Employee.

        POST /api/odoo-attendance/push/register
        Authorization: Bearer <access_token>
        Body: { "fcm_token": "<token>" }
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            employee_app, _hr_employee = auth_result

            try:
                data = json.loads(request.httprequest.data or b'{}')
            except Exception:
                return response_helper.validation_error_response('Invalid JSON in request body')

            token = (data.get('fcm_token') or '').strip()
            if not token:
                return response_helper.validation_error_response('Missing required field: fcm_token')

            employee_app.sudo().write(
                {
                    'fcm_token': token,
                    'fcm_token_updated_at': fields.Datetime.now(),
                }
            )

            _logger.info(
                'FCM token registered (employee_app_id=%s, token_len=%s, token_suffix=%s)',
                employee_app.id,
                len(token),
                token[-8:] if len(token) >= 8 else token,
            )
            return response_helper.success_response({'registered': True})
        except Exception as e:
            _logger.exception('Error in push/register: %s', e)
            return response_helper.server_error_response('An error occurred')
