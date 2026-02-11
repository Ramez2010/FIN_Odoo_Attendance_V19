# -*- coding: utf-8 -*-
import logging
from odoo import models, fields
from odoo.exceptions import UserError

from ..utils import license_helper

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tracking_enabled = fields.Boolean(
        string='Live Tracking Enabled',
        help='If checked, this employee will appear on the Live Map if a recent location is available.'
    )
    tracking_device_identifier = fields.Char(
        string='Device Identifier',
        help='Unique ID for the tracking device (e.g. mobile device ID or MDM ID).'
    )

    # Lightweight state for live-location requests
    live_location_request_at = fields.Datetime(
        string='Last Live Location Request At',
        help='Timestamp when a live-location request was last sent to this employee.'
    )
    live_location_request_state = fields.Selection([
        ('none', 'None'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
    ], string='Live Location Request State', default='none')
    live_location_request_attempts = fields.Integer(
        string='Live Location Request Attempts',
        default=0,
        help='Number of attempts made to request a live location since the last success.'
    )

    def action_request_live_location(self):
        """
        Sends a silent FCM push notification to the employee's mobile device
        to request an immediate location update.
        """
        ok, msg = license_helper.is_subscription_active(self.env, allow_refresh=True)
        if not ok:
            raise UserError(msg or 'Subscription required.')

        for record in self:
            # Skip employees who are not currently checked-in
            if getattr(record, 'attendance_state', None) != 'checked_in':
                continue

            # Find the active mobile app account for this HR employee
            app_employee = self.env['odoo.attendance.employee'].sudo().search([
                ('employee_id', '=', record.id),
                ('is_active', '=', True)
            ], limit=1)
            
            if not app_employee:
                _logger.warning('No mobile app account for employee id=%s, skipping live location request', record.id)
                continue

            token = (app_employee.fcm_token or '').strip()
            if not token:
                _logger.warning('No FCM token for employee id=%s app_id=%s, skipping live location request', record.id, app_employee.id)
                record.sudo().write({'live_location_request_state': 'failed'})
                continue
                
            try:
                from ..utils import push_helper
                ok, msg = push_helper.send_fcm_push(
                    env=self.env,
                    token=token,
                    title='', # Silent push: no title/body
                    body='',
                    data={
                        'kind': 'request_location'
                    },
                    silent=True,
                )
                if ok:
                    record.sudo().write({
                        'live_location_request_at': fields.Datetime.now(),
                        'live_location_request_state': 'pending',
                        'live_location_request_attempts': (record.live_location_request_attempts or 0) + 1,
                    })
                    _logger.info('Live location request sent: employee_id=%s app_id=%s token_last6=%s', record.id, app_employee.id, token[-6:])
                else:
                    record.sudo().write({
                        'live_location_request_at': fields.Datetime.now(),
                        'live_location_request_state': 'failed',
                    })
                    _logger.warning('Live location request failed: employee_id=%s app_id=%s reason=%s', record.id, app_employee.id, msg)
            except Exception as e:
                _logger.exception('Error sending live location request for employee %s: %s', record.id, str(e))
        return True

    def retry_live_location_requests(self, max_attempts=2, retry_after_seconds=10):
        """
        Find employees with a pending or failed live-location request and retry sending.
        - max_attempts: how many total attempts to make before giving up
        - retry_after_seconds: minimum seconds since last attempt to retry
        This method is safe to call from a scheduled job or manually from the shell.
        """
        ok, msg = license_helper.is_subscription_active(self.env, allow_refresh=True)
        if not ok:
            _logger.warning('Retry live location requests blocked by subscription check: %s', msg)
            return True

        from datetime import datetime, timedelta
        now = fields.Datetime.to_datetime(fields.Datetime.now())
        cutoff = now - timedelta(seconds=retry_after_seconds)

        # Search for employees where requests are pending or failed but attempts < max_attempts.
        # We cannot search on the non-stored computed field `attendance_state`, so
        # filter by tracking_enabled and request_state and check attendance per-record.
        candidates = self.search([
            ('tracking_enabled', '=', True),
            ('live_location_request_state', 'in', ('pending','failed')),
            ('live_location_request_attempts', '<', max_attempts)
        ])

        for emp in candidates:
            # Skip if not currently checked-in (attendance_state is non-stored)
            if getattr(emp, 'attendance_state', None) != 'checked_in':
                continue

            last_at = emp.live_location_request_at
            if last_at:
                try:
                    last_dt = fields.Datetime.to_datetime(last_at)
                except Exception:
                    last_dt = None
            else:
                last_dt = None

            if last_dt and last_dt > cutoff:
                # Too recent, skip
                continue

            # Attempt to send again
            try:
                app_employee = self.env['odoo.attendance.employee'].sudo().search([
                    ('employee_id', '=', emp.id),
                    ('is_active', '=', True)
                ], limit=1)
                if not app_employee:
                    emp.sudo().write({'live_location_request_state': 'failed'})
                    continue
                token = (app_employee.fcm_token or '').strip()
                if not token:
                    emp.sudo().write({'live_location_request_state': 'failed'})
                    continue

                from ..utils import push_helper
                ok, msg = push_helper.send_fcm_push(
                    env=self.env,
                    token=token,
                    title='', body='', data={'kind': 'request_location'}, silent=True,
                )
                if ok:
                    emp.sudo().write({
                        'live_location_request_at': fields.Datetime.now(),
                        'live_location_request_state': 'pending',
                        'live_location_request_attempts': (emp.live_location_request_attempts or 0) + 1,
                    })
                    _logger.info('Retry live location request sent: employee_id=%s app_id=%s token_last6=%s', emp.id, app_employee.id, token[-6:])
                else:
                    emp.sudo().write({
                        'live_location_request_at': fields.Datetime.now(),
                        'live_location_request_state': 'failed',
                    })
                    _logger.warning('Retry live location request failed: employee_id=%s app_id=%s reason=%s', emp.id if emp else None, app_employee.id if app_employee else None, msg)
            except Exception as e:
                _logger.exception('Error retrying live location request for employee %s: %s', emp.id, str(e))
        return True
