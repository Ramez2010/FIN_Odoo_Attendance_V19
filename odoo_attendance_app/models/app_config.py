# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import pytz

from ..utils.geofence_helper import get_geofence_locations, haversine_km

_logger = logging.getLogger(__name__)


class OdooAttendanceAppConfig(models.Model):
    _name = 'odoo.attendance.app.config'
    _description = 'FIN Attendance Configuration'
    _rec_name = 'name'

    name = fields.Char(default='Settings', readonly=True)
    selfie_retention_days = fields.Integer(string='Selfie Retention (days)', default=60)
    cron_interval_number = fields.Integer(string='Cleanup Interval', default=1)
    cron_interval_type = fields.Selection(
        [
            ('minutes', 'Minutes'),
            ('hours', 'Hours'),
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
        ],
        string='Cleanup Interval Unit',
        default='days',
        required=True,
    )

    license_server_url = fields.Char(string='License Server URL')
    license_key = fields.Char(string='License Key')
    license_grace_days = fields.Integer(string='License Grace (days)', default=7)

    fcm_server_key = fields.Char(
        string='FCM Server Key (Android Push - Legacy)',
        help='Deprecated: Firebase Cloud Messaging Legacy server key. Most new Firebase projects no longer support Legacy HTTP.',
    )
    fcm_project_id = fields.Char(
        string='FCM Project ID (Android Push)',
        help='Firebase/Google Cloud project_id used for FCM HTTP v1. If empty, it will be read from the service account JSON.',
    )
    fcm_service_account_json = fields.Text(
        string='FCM Service Account JSON (Android Push)',
        help='Service account JSON (Firebase Admin SDK) used for FCM HTTP v1. Keep this secret.',
    )

    google_maps_api_key = fields.Char(
        string='Google Maps API Key',
        help='Used by Live Map. Stored in system parameters as odoo_attendance_app.google_maps_api_key.',
    )

    far_away_monitoring_enabled = fields.Boolean(
        string='Far-away Alerts (sites)',
        default=False,
        help=(
            'When enabled, the system checks every 30 minutes whether checked-in employees '
            'are outside their project geofence radius and notifies their managers.'
        ),
    )

    license_status = fields.Char(string='License Status', compute='_compute_license_state', store=False)
    license_valid_until = fields.Datetime(string='Valid Until', compute='_compute_license_state', store=False)
    license_last_check = fields.Datetime(string='Last Check', compute='_compute_license_state', store=False)
    license_employee_limit = fields.Integer(string='Employee Limit', compute='_compute_license_state', store=False)
    license_employee_count = fields.Integer(string='Active Employees', compute='_compute_license_state', store=False)
    license_last_error = fields.Text(string='Last License Error', compute='_compute_license_state', store=False)
    message_timezone = fields.Selection(
        [(tz, tz) for tz in pytz.common_timezones],
        string='Messages Timezone',
        help='Timezone used to compute scheduled/repeat message times.',
    )

    @api.constrains('selfie_retention_days', 'cron_interval_number')
    def _check_positive(self):
        for record in self:
            if record.selfie_retention_days < 0:
                raise ValidationError('Selfie retention days must be 0 or greater.')
            if record.cron_interval_number <= 0:
                raise ValidationError('Cleanup interval must be greater than 0.')
            if record.license_grace_days < 0:
                raise ValidationError('License grace days must be 0 or greater.')

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        icp = self.env['ir.config_parameter'].sudo()

        def _get_int(key, default):
            raw = icp.get_param(key, default=str(default))
            try:
                return int(raw)
            except Exception:
                return default

        result.setdefault(
            'selfie_retention_days',
            _get_int('odoo_attendance_app.selfie_retention_days', 60),
        )
        result.setdefault(
            'license_grace_days',
            _get_int('odoo_attendance_app.license_grace_days', 7),
        )
        result.setdefault(
            'license_server_url',
            (icp.get_param('odoo_attendance_app.license_server_url', default='') or '').strip(),
        )
        result.setdefault(
            'license_key',
            (icp.get_param('odoo_attendance_app.license_key', default='') or '').strip(),
        )
        result.setdefault(
            'fcm_server_key',
            (icp.get_param('odoo_attendance_app.fcm_server_key', default='') or '').strip(),
        )
        result.setdefault(
            'fcm_project_id',
            (icp.get_param('odoo_attendance_app.fcm_project_id', default='') or '').strip(),
        )
        result.setdefault(
            'fcm_service_account_json',
            (icp.get_param('odoo_attendance_app.fcm_service_account_json', default='') or '').strip(),
        )
        result.setdefault(
            'message_timezone',
            (icp.get_param('odoo_attendance_app.message_timezone', default='') or '').strip(),
        )
        result.setdefault(
            'google_maps_api_key',
            (icp.get_param('odoo_attendance_app.google_maps_api_key', default='') or '').strip(),
        )
        cron = self.env.ref(
            'odoo_attendance_app.ir_cron_cleanup_attendance_selfies',
            raise_if_not_found=False,
        )
        if cron:
            result.setdefault('cron_interval_number', cron.interval_number or 1)
            result.setdefault('cron_interval_type', cron.interval_type or 'days')

        return result

    def _compute_license_state(self):
        from ..utils import license_helper

        for record in self:
            cfg = license_helper.get_license_config(record.env)
            cached = license_helper.get_cached_license_state(record.env)
            valid_until = cached.get('valid_until')
            last_check = cached.get('last_check')
            server_status = (cached.get('status') or '').strip().lower()

            record.license_valid_until = valid_until
            record.license_last_check = last_check
            record.license_employee_limit = cached.get('employee_limit') or 0
            record.license_employee_count = license_helper.get_employee_count(record.env)
            record.license_last_error = cached.get('last_error') or ''

            # Display an "effective" status consistent with enforcement:
            # - if not configured -> unconfigured
            # - if server revoked/blocked -> blocked
            # - else derive from valid_until + grace window
            if not cfg.get('license_key') or not cfg.get('license_server_url'):
                record.license_status = 'unconfigured'
                continue

            if server_status in ('revoked', 'blocked'):
                record.license_status = 'blocked'
                continue

            # If the last check failed (invalid key, server unreachable, etc), show that explicitly.
            # Otherwise the UI may still display "active" based on a previously cached valid_until.
            if server_status in ('error', 'unconfigured'):
                record.license_status = server_status
                continue

            if not valid_until:
                record.license_status = 'unknown'
                continue

            grace_days = max(int(cfg.get('grace_days') or 7), 0)
            now = license_helper._utcnow()
            grace_until = valid_until + license_helper.timedelta(days=grace_days)
            if now <= valid_until:
                record.license_status = 'active'
            elif now <= grace_until:
                record.license_status = 'grace'
            else:
                record.license_status = 'expired'

    def action_check_license_now(self):
        from ..utils import license_helper

        self.ensure_one()
        # Ensure current form values are persisted to system parameters first
        # so the license check uses the latest URL/key even if the user didn't
        # manually save before clicking the button.
        self._apply()
        ok, msg = license_helper.refresh_license_from_server(self.env)

        # Surface whether we actually received a signed token that the mobile app requires.
        cached_token = license_helper.get_cached_license_token(self.env) if ok else ''
        token_ok = bool(cached_token and not license_helper._is_license_token_expired(cached_token))
        if ok and not token_ok:
            msg = (msg or '').strip() or 'License is valid, but no signed license token was returned by the license server.'
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'License Check',
                'message': 'License is valid.' if (ok and token_ok) else (msg or 'License check failed.'),
                'sticky': False,
                'type': 'success' if (ok and token_ok) else 'warning',
                # Refresh the form so computed "Current Status" fields update immediately.
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }
        return notification

    @api.model
    def _cron_license_check(self):
        from ..utils import license_helper

        license_helper.refresh_license_from_server(self.env)
        return True

    def _cron_far_away_monitoring(self):
        record = self.search([], order='id desc', limit=1)
        if not record:
            return True
        record._run_far_away_monitoring()
        return True

    def _run_far_away_monitoring(self):
        self.ensure_one()
        if not self.far_away_monitoring_enabled:
            return True

        Attendance = self.env['hr.attendance'].sudo()
        Location = self.env['hr.employee.location.latest'].sudo()
        EmployeeApp = self.env['odoo.attendance.employee'].sudo()

        checked_in = Attendance.search([('check_out', '=', False)])
        alerts_sent = 0
        for attendance in checked_in:
            analytic = attendance.x_analytic_account_id
            if not analytic or not analytic.x_enable_geofence:
                continue

            locations = get_geofence_locations(analytic)
            if not locations:
                continue

            hr_employee = attendance.employee_id
            location_record = Location.search([('employee_id', '=', hr_employee.id)], limit=1)
            if not location_record or location_record.reachable_status != 'reachable':
                continue

            lat = location_record.latitude
            lng = location_record.longitude
            entries = [
                (haversine_km(lat_cfg, lng_cfg, lat, lng), radius, lat_cfg, lng_cfg)
                for lat_cfg, lng_cfg, radius in locations
            ]
            if not entries:
                continue
            if any(distance <= radius for distance, radius, _, _ in entries):
                continue

            actual_distance_km, allowed_radius_km, loc_lat, loc_lng = min(entries, key=lambda entry: entry[0] - entry[1])
            employee_app = EmployeeApp.search([('employee_id', '=', hr_employee.id)], limit=1)
            if not employee_app:
                continue

            manager_hr = employee_app.manager_employee_ids
            if not manager_hr:
                continue

            manager_apps = EmployeeApp.with_context(prefetch_fields=False).search([
                ('employee_id', 'in', manager_hr.ids),
                ('is_active', '=', True),
            ])
            if not manager_apps:
                continue

            self._notify_managers_far_away(
                hr_employee=hr_employee,
                analytic_account=analytic,
                location_record=location_record,
                actual_distance_km=actual_distance_km,
                allowed_radius_km=allowed_radius_km,
                manager_apps=manager_apps,
                location_lat=loc_lat,
                location_lng=loc_lng,
            )
            alerts_sent += 1

        if alerts_sent:
            _logger.info('Far-away alert cron sent %d notifications', alerts_sent)
        return True

    def _notify_managers_far_away(
        self,
        hr_employee,
        analytic_account,
        location_record,
        actual_distance_km,
        allowed_radius_km,
        manager_apps,
        location_lat,
        location_lng,
    ):
        excess_km = max(actual_distance_km - allowed_radius_km, 0)
        map_url = (
            f'https://www.google.com/maps/search/?api=1&query='
            f'{location_record.latitude:.6f}%2C{location_record.longitude:.6f}'
        )
        lines = [
            f'{hr_employee.display_name} is {actual_distance_km:.2f} km from '
            f'{analytic_account.name or "the project"} locations.',
            f'Allowed radius: {allowed_radius_km:.2f} km (exceeded by {excess_km:.2f} km).',
            f'Configured location: {location_lat:.6f}, {location_lng:.6f}',
            f'Current location: {location_record.latitude:.6f}, {location_record.longitude:.6f}',
            f'Timestamp (UTC): {location_record.timestamp_utc}',
            f'Map: {map_url}',
        ]
        try:
            message = self.env['odoo.attendance.inbox.message'].sudo().create(
                {
                    'name': f'Far Away Alert: {hr_employee.display_name}',
                    'body': '\n'.join(lines),
                    'message_type': 'attendance',
                    'target_all': False,
                    'target_employee_app_ids': [(6, 0, manager_apps.ids)],
                }
            )
            message.action_send_now()
        except Exception as exc:
            _logger.warning(
                'Failed to send far-away alert for employee=%s: %s',
                hr_employee.display_name,
                exc,
            )

    @api.model_create_multi
    def create(self, vals_list):
        if self.search_count([]) > 0:
            raise ValidationError('Only one configuration record is allowed.')
        for vals in vals_list:
            vals.setdefault('name', 'Settings')
        records = super().create(vals_list)
        records._apply()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._apply()
        return result

    def _apply(self):
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('odoo_attendance_app.selfie_retention_days', str(self.selfie_retention_days))
        icp.set_param('odoo_attendance_app.license_server_url', (self.license_server_url or '').strip())
        icp.set_param('odoo_attendance_app.license_key', (self.license_key or '').strip())
        icp.set_param('odoo_attendance_app.license_grace_days', str(self.license_grace_days))
        icp.set_param('odoo_attendance_app.fcm_server_key', (self.fcm_server_key or '').strip())
        icp.set_param('odoo_attendance_app.fcm_project_id', (self.fcm_project_id or '').strip())
        icp.set_param('odoo_attendance_app.fcm_service_account_json', (self.fcm_service_account_json or '').strip())
        icp.set_param('odoo_attendance_app.message_timezone', (self.message_timezone or '').strip())
        icp.set_param('odoo_attendance_app.google_maps_api_key', (self.google_maps_api_key or '').strip())

        cron = self.env.ref(
            'odoo_attendance_app.ir_cron_cleanup_attendance_selfies',
            raise_if_not_found=False,
        )
        if cron:
            cron.sudo().write(
                {
                    'interval_number': self.cron_interval_number,
                    'interval_type': self.cron_interval_type,
                    'active': True,
                }
            )

    @api.model
    def action_open_settings(self):
        """
        Open the singleton settings record (create it if missing).
        This avoids users accidentally creating a second record and hitting the constraint.
        """
        record = self.search([], order='id desc', limit=1)
        if not record:
            record = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Settings',
            'res_model': 'odoo.attendance.app.config',
            'view_mode': 'form',
            'res_id': record.id,
            'target': 'current',
            'context': {'create': False, 'delete': False},
        }
