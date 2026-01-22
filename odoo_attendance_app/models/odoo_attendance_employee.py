# -*- coding: utf-8 -*-
import json
import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ..utils.password_helper import hash_password
from ..utils import license_helper

_logger = logging.getLogger(__name__)


class OdooAttendanceEmployee(models.Model):
    """
    Stores employee credentials for mobile app authentication.
    Each employee has app-specific username/password separate from Odoo users.
    Implements device binding (one device per employee).
    """
    _name = 'odoo.attendance.employee'
    _description = 'FIN Attendance Employee'
    _rec_name = 'username'
    
    username = fields.Char(
        string='Username',
        required=True,
        index=True,
        help='Unique username for mobile app login'
    )
    password_hash = fields.Char(
        string='Password Hash',
        required=True,
        help='bcrypt hashed password (never store plain text)'
    )
    password = fields.Char(
        string='Set Password',
        store=False,
        help='Enter a new password to update the hash'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        # Enforce subscription employee limit on creation (active employees only)
        active_new = sum(1 for vals in vals_list if vals.get('is_active', True))
        if active_new:
            ok, msg = license_helper.is_subscription_active(self.env, allow_refresh=True)
            if not ok:
                raise ValidationError(_(msg))

            cached = license_helper.get_cached_license_state(self.env)
            limit = cached.get('employee_limit') or 0
            if limit > 0:
                current = license_helper.get_employee_count(self.env)
                if current + active_new > limit:
                    raise ValidationError(
                        _(
                            'Your subscription includes %s employees and you have reached the maximum. '
                            'Please upgrade your subscription to add more employees.'
                        )
                        % limit
                    )

        # Hash passwords when provided
        for vals in vals_list:
            if vals.get('password'):
                vals['password_hash'] = hash_password(vals['password'])
            if 'password_hash' not in vals and not vals.get('password'):
                # Fallback or error could be raised here, but we'll let Odoo required=True handle missing field if neither exist
                pass

        return super(OdooAttendanceEmployee, self).create(vals_list)

    def write(self, vals):
        # Enforce subscription employee limit when activating an employee
        if vals.get('is_active') is True:
            ok, msg = license_helper.is_subscription_active(self.env, allow_refresh=True)
            if not ok:
                raise ValidationError(_(msg))

            cached = license_helper.get_cached_license_state(self.env)
            limit = cached.get('employee_limit') or 0
            if limit > 0:
                # Count currently active excluding records being written if currently inactive
                current = license_helper.get_employee_count(self.env)
                activating = len(self.filtered(lambda r: not r.is_active))
                if current + activating > limit:
                    raise ValidationError(
                        _(
                            'Your subscription includes %s employees and you have reached the maximum. '
                            'Please upgrade your subscription to add more employees.'
                        )
                        % limit
                    )

        if vals.get('password'):
            vals['password_hash'] = hash_password(vals['password'])
        return super(OdooAttendanceEmployee, self).write(vals)
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
        help='Link to HR Employee record'
    )
    manager_employee_ids = fields.Many2many(
        'hr.employee',
        'odoo_attendance_employee_manager_rel',
        'employee_app_id',
        'manager_id',
        string='Manager',
        help='Managers who should receive check-in/out notifications for this employee.',
    )
    selfie_policy_checkin = fields.Selection(
        [
            ('optional', 'Optional'),
            ('required', 'Required'),
        ],
        string='Check-in Selfie',
        default='optional',
        required=True,
        help='Whether a selfie is required when checking in from the mobile app.',
    )
    selfie_policy_checkout = fields.Selection(
        [
            ('optional', 'Optional'),
            ('required', 'Required'),
        ],
        string='Check-out Selfie',
        default='optional',
        required=True,
        help='Whether a selfie is required when checking out from the mobile app.',
    )
    device_id = fields.Char(
        string='Device ID',
        index=True,
        help='Platform-specific device identifier for binding'
    )
    fcm_token = fields.Char(
        string='FCM Token',
        index=True,
        help='Firebase Cloud Messaging token (Android-only) used for push notifications.',
    )
    fcm_token_updated_at = fields.Datetime(
        string='FCM Token Updated At',
        readonly=True,
    )
    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, employee cannot login to mobile app'
    )
    last_login = fields.Datetime(
        string='Last Login',
        readonly=True
    )
    
    # Relational fields
    session_ids = fields.One2many(
        'odoo.attendance.session',
        'employee_app_id',
        string='Sessions'
    )
    
    _sql_constraints = [
        ('unique_username', 'UNIQUE(username)', 
         'Username must be unique! This username is already taken.'),
        ('unique_employee', 'UNIQUE(employee_id)', 
         'An app user already exists for this employee!'),
    ]
    
    @api.constrains('username')
    def _check_username(self):
        """Validate username format"""
        for record in self:
            if record.username:
                if len(record.username) < 3:
                    raise ValidationError(_('Username must be at least 3 characters long.'))
                if not record.username.replace('.', '').replace('_', '').replace('-', '').isalnum():
                    raise ValidationError(_('Username can only contain letters, numbers, dots, underscores, and hyphens.'))

    
    def update_last_login(self):
        """Update last login timestamp"""
        self.ensure_one()
        self.write({'last_login': fields.Datetime.now()})
    
    def bind_device(self, device_id):
        """Bind employee to a device"""
        self.ensure_one()
        if self.device_id and self.device_id != device_id:
            raise ValidationError(_(
                'This employee is already bound to another device. '
                'Contact administrator to reset device binding.'
            ))
        self.write({'device_id': device_id})
    
    def reset_device_binding(self):
        """Admin function to reset device binding"""
        self.write({'device_id': False})
        # Also invalidate all sessions
        self.session_ids.sudo().unlink()
        return True
    
    def verify_device(self, device_id):
        """Check if device is authorized for this employee"""
        self.ensure_one()
        if not self.device_id:
            # First login - no device bound yet
            return True
        return self.device_id == device_id

    def send_push_notification(self, title, body, data=None):
        """
        Send a push notification to the employee's mobile device via FCM.
        :param title: Notification title
        :param body: Notification body
        :param data: Optional dictionary of data to send with the notification
        """
        self.ensure_one()
        if not self.fcm_token:
            _logger.info("No FCM token for employee %s, cannot send push notification.", self.employee_id.name)
            return False

        fcm_server_key = self.env['ir.config_parameter'].sudo().get_param('odoo_attendance_app.fcm_server_key')
        if not fcm_server_key:
            _logger.error("FCM Server Key not configured in System Parameters. Cannot send push notification.")
            return False

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'key={fcm_server_key}',
        }
        
        # FCM message structure
        message = {
            'to': self.fcm_token,
            'priority': 'high',
            'notification': {
                'title': title,
                'body': body,
            },
            'data': data or {}, # Custom data payload
        }

        try:
            response = requests.post('https://fcm.googleapis.com/fcm/send', headers=headers, data=json.dumps(message), timeout=5)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            result = response.json()
            if result.get('failure') or result.get('canonical_ids'):
                _logger.warning("FCM notification failed or token invalid for employee %s: %s", self.employee_id.name, result)
                # Optionally, clear invalid FCM token here: self.write({'fcm_token': False})
            else:
                _logger.info("FCM notification sent to employee %s: %s", self.employee_id.name, result)
            return True
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to send FCM notification to employee %s: %s", self.employee_id.name, e)
            return False
