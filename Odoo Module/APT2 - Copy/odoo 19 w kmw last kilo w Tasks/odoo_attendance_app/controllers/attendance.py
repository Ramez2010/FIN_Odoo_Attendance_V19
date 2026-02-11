# -*- coding: utf-8 -*-
import json
import base64
import logging
from datetime import datetime
from io import BytesIO
import zipfile
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError
from .employee import authenticate_request
from .subscription import require_active_subscription
from ..utils import response_helper
from ..utils.geofence_helper import get_geofence_locations, haversine_km

_logger = logging.getLogger(__name__)



def _format_google_maps_location(gps_address, gps_lat, gps_lng):
    if gps_address:
        return gps_address
    if gps_lat is None or gps_lng is None:
        return ''
    try:
        lat_val = float(gps_lat)
        lng_val = float(gps_lng)
        return f'https://www.google.com/maps/search/?api=1&query={lat_val:.6f}%2C{lng_val:.6f}'
    except Exception:
        return f'https://www.google.com/maps/search/?api=1&query={gps_lat}%2C{gps_lng}'


def _parse_float(raw, label):
    if raw in (None, ''):
        return None
    try:
        return float(str(raw).strip())
    except Exception:
        raise ValidationError(f'{label} must be a number.')


def _parse_int(raw, label):
    if raw in (None, ''):
        return None
    try:
        return int(str(raw).strip())
    except Exception:
        raise ValidationError(f'{label} is invalid.')


def _is_geofence_exempt(analytic_account, hr_employee):
    if not analytic_account or not hr_employee:
        return False
    exception_ids = analytic_account.x_geofence_exception_employee_ids
    if not exception_ids:
        return False
    return hr_employee.id in exception_ids.ids


def _send_manager_attendance_notification(*, employee_app, hr_employee, event, attendance, analytic_account, note):
    """
    Create an in-app inbox notification for the employee's manager (if configured).
    Managers receive notifications in the same mobile app (they must have a Mobile App Employee account).
    """
    try:
        manager_hrs = employee_app.manager_employee_ids
        if not manager_hrs:
            return

        manager_apps = request.env['odoo.attendance.employee'].sudo().with_context(prefetch_fields=False).search(
            [('employee_id', 'in', manager_hrs.ids), ('is_active', '=', True)],
        )
        if not manager_apps:
            return

        msg_subject = 'Check-in update' if event == 'check_in' else 'Check-out update'
        when = (attendance.check_in if event == 'check_in' else attendance.check_out) or fields.Datetime.now()
        project_name = analytic_account.name if analytic_account else ''
        employee_name = hr_employee.name or ''

        gps_lat = attendance.x_checkin_gps_lat if event == 'check_in' else attendance.x_checkout_gps_lat
        gps_lng = attendance.x_checkin_gps_lng if event == 'check_in' else attendance.x_checkout_gps_lng
        gps_accuracy = attendance.x_checkin_gps_accuracy if event == 'check_in' else attendance.x_checkout_gps_accuracy
        gps_address = attendance.x_checkin_gps_address if event == 'check_in' else attendance.x_checkout_gps_address
        map_url = ''
        if gps_lat is not None and gps_lng is not None:
            lat_str = str(gps_lat).strip()
            lng_str = str(gps_lng).strip()
            if lat_str and lng_str:
                try:
                    lat_val = float(lat_str)
                    lng_val = float(lng_str)
                    coord = f'{lat_val:.6f}%2C{lng_val:.6f}'
                except Exception:
                    coord = f'{lat_str}%2C{lng_str}'
                map_url = f'https://www.google.com/maps/search/?api=1&query={coord}'

        if event == 'check_in':
            headline = f'{employee_name} checked in.' if employee_name else 'Employee checked in.'
        else:
            headline = f'{employee_name} checked out.' if employee_name else 'Employee checked out.'

        lines = [headline]
        if project_name:
            lines.append(f'Project: {project_name}')
        lines.append(f'Time: {when}')
        if note:
            lines.append(f'Note: {note}')
        if gps_lat and gps_lng:
            gps_line = f'GPS: {gps_lat},{gps_lng}'
            if gps_accuracy:
                gps_line += f' (accuracy {gps_accuracy}m)'
            lines.append(gps_line)
        if gps_address:
            lines.append(f'Address: {gps_address}')
        if map_url:
            lines.append(f'Map: {map_url}')

        msg_body = '\n'.join(lines)

        msg = request.env['odoo.attendance.inbox.message'].sudo().create(
            {
                'name': msg_subject,
                'body': msg_body,
                'message_type': 'attendance',
                'target_all': False,
                'target_employee_app_ids': [(6, 0, manager_apps.ids)],
            }
        )
        msg.action_send_now()
    except Exception as e:
        _logger.warning(f'Failed to send manager notification: {e}')


class AttendanceController(http.Controller):
    """
    Attendance check-in/out and history endpoints.
    """
    
    @http.route('/api/odoo-attendance/attendance/check-in', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def check_in(self, **kwargs):
        """
        Create attendance check-in with GPS and optional selfie.
        
        POST /api/odoo-attendance/attendance/check-in
        Authorization: Bearer <access_token>
        
        Request body:
        {
            "analytic_account_id": 10,
            "gps_lat": 30.0444,
            "gps_lng": 31.2357,
            "gps_accuracy": 12.5,
            "gps_address": "123 Main St, Cairo, Egypt",
            "selfie_base64": "iVBORw0KGgoAAAANS..."  // optional
        }
        
        Response:
        {
            "success": true,
            "data": {
                "attendance_id": 501,
                "check_in": "2026-01-05T17:30:00",
                "analytic_account": {...}
            }
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
            
            # Parse request body
            try:
                data = json.loads(request.httprequest.data)
            except:
                return response_helper.validation_error_response('Invalid JSON in request body')
            
            # Validate required fields
            analytic_account_id = data.get('analytic_account_id')
            gps_lat = data.get('gps_lat')
            gps_lng = data.get('gps_lng')
            gps_accuracy = data.get('gps_accuracy')
            gps_address = data.get('gps_address', '')
            selfie_base64 = data.get('selfie_base64')
            gallery_images = data.get('gallery_images') or []
            checkin_note = (data.get('note') or '').strip()

            if not checkin_note:
                return response_helper.validation_error_response('Check-in note is required.')
            
            if not analytic_account_id:
                return response_helper.validation_error_response('Missing required field: analytic_account_id')

            if not isinstance(gallery_images, list):
                return response_helper.validation_error_response('gallery_images must be a list.')
            
            # Check if employee already has open attendance
            Attendance = request.env['hr.attendance'].sudo()
            open_attendance = Attendance.search([
                ('employee_id', '=', hr_employee.id),
                ('check_out', '=', False)
            ], limit=1)
            
            if open_attendance:
                return response_helper.validation_error_response(
                    'You are already checked in. Please check out first.'
                )
            
            # Verify employee has access to this analytic account
            AnalyticAccount = request.env['account.analytic.account'].sudo()
            analytic_account = AnalyticAccount.search([
                ('id', '=', analytic_account_id),
                '|', ('x_allow_all_employees', '=', True),
                     ('x_allowed_employee_ids', 'in', [hr_employee.id])
            ], limit=1)

            if not analytic_account:
                return response_helper.forbidden_response(
                    'You do not have access to this analytic account.'
                )

            is_driver = bool(employee_app.is_driver)
            vehicle = None
            vehicle_id = None
            start_kilometrage = None
            if is_driver:
                if not hr_employee.user_id:
                    return response_helper.validation_error_response(
                        'Driver must be linked to a user account.'
                    )
                vehicle_id = _parse_int(data.get('vehicle_id'), 'Vehicle')
                if not vehicle_id:
                    return response_helper.validation_error_response(
                        'Vehicle is required for drivers.'
                    )
                start_kilometrage = _parse_float(
                    data.get('kilometrage') if 'kilometrage' in data else data.get('start_kilometrage'),
                    'Kilometrage'
                )
                if start_kilometrage is None:
                    return response_helper.validation_error_response(
                        'Kilometrage is required for drivers.'
                    )
                Vehicle = request.env['odoo.attendance.vehicle'].sudo()
                vehicle = Vehicle.search([
                    ('id', '=', vehicle_id),
                    ('allowed_employee_ids', 'in', [employee_app.id])
                ], limit=1)
                if not vehicle:
                    return response_helper.forbidden_response(
                        'You are not allowed to use this vehicle.'
                    )
                if vehicle.current_kilometrage is not None and start_kilometrage is not None:
                    if start_kilometrage < float(vehicle.current_kilometrage):
                        return response_helper.validation_error_response(
                            'Kilometrage cannot be less than the last recorded value.'
                        )
                FleetTrip = request.env['odoo.attendance.fleet.trip'].sudo()
                existing_trip = FleetTrip.search([
                    ('driver_user_id', '=', hr_employee.user_id.id),
                    ('state', '=', 'in_progress'),
                    ('trip_end_date_time', '=', False)
                ], limit=1, order='trip_start_date_time desc')
                if existing_trip:
                    return response_helper.validation_error_response(
                        'You already have an open trip. Please check out first.'
                    )

            # Selfie policy: employee or project can require a selfie
            employee_requires_selfie = (employee_app.selfie_policy_checkin or 'optional') == 'required'
            project_requires_selfie = (analytic_account.x_selfie_policy_checkin or 'optional') == 'required'
            if (employee_requires_selfie or project_requires_selfie) and not selfie_base64:
                _logger.info(
                    'Check-in rejected: selfie required (employee_required=%s project_required=%s employee_app_id=%s analytic_account_id=%s)',
                    employee_requires_selfie,
                    project_requires_selfie,
                    employee_app.id,
                    analytic_account.id,
                )
                return response_helper.validation_error_response('please take selfie and try again')

            # Geofence validation: if radius set (>0), require GPS and enforce distance
            locations = get_geofence_locations(analytic_account)
            geofence_exempt = _is_geofence_exempt(analytic_account, hr_employee)
            # Skip geofence unless enabled and locations are configured
            if analytic_account.x_enable_geofence and locations and not geofence_exempt:
                if gps_lat is None or gps_lng is None:
                    return response_helper.validation_error_response(
                        'GPS coordinates are required for this analytic account.'
                    )

                within_radius = False
                for lat_cfg, lng_cfg, radius in locations:
                    distance_km = haversine_km(
                        lat_cfg,
                        lng_cfg,
                        float(gps_lat),
                        float(gps_lng),
                    )
                    if distance_km <= radius:
                        within_radius = True
                        break
                if not within_radius:
                    _logger.info(
                        'Check-in geofence rejected: employee_app_id=%s analytic_account_id=%s enabled=%s gps_lat=%s gps_lng=%s',
                        employee_app.id,
                        analytic_account.id,
                        bool(analytic_account.x_enable_geofence),
                        gps_lat,
                        gps_lng,
                    )
                    return response_helper.forbidden_response(
                        'You are not near the project location.'
                    )

            # Create attendance record
            now = fields.Datetime.now()
            attendance_vals = {
                'employee_id': hr_employee.id,
                'check_in': now,
                'x_analytic_account_id': analytic_account_id,
                'x_checkin_gps_lat': gps_lat,
                'x_checkin_gps_lng': gps_lng,
                'x_checkin_gps_accuracy': gps_accuracy,
                'x_checkin_gps_address': gps_address,
                'x_checkin_note': checkin_note,
            }
            if is_driver:
                attendance_vals.update({
                    'x_vehicle_id': vehicle.id,
                    'x_start_kilometrage': start_kilometrage,
                })
            
            attendance = Attendance.create(attendance_vals)

            fleet_trip = None
            if is_driver:
                start_location = _format_google_maps_location(gps_address, gps_lat, gps_lng)
                fleet_trip = request.env['odoo.attendance.fleet.trip'].sudo().create({
                    'trip_start_date_time': now,
                    'driver_user_id': hr_employee.user_id.id,
                    'vehicle_id': vehicle.id,
                    'analytic_account_id': analytic_account.id if analytic_account else None,
                    'start_google_maps_location': start_location,
                    'start_kilometrage': start_kilometrage,
                })
                attendance.write({'x_fleet_trip_id': fleet_trip.id})
            
            # Update latest location instantly on check-in
            if gps_lat and gps_lng:
                try:
                    Location = request.env['hr.employee.location.latest'].sudo()
                    existing = Location.search([('employee_id', '=', hr_employee.id)], limit=1)
                    loc_vals = {
                        'employee_id': hr_employee.id,
                        'latitude': float(gps_lat),
                        'longitude': float(gps_lng),
                        'accuracy': float(gps_accuracy or 0.0),
                        'timestamp_utc': fields.Datetime.now(),
                        'source': 'mobile',
                    }
                    if existing:
                        existing.write(loc_vals)
                    else:
                        Location.create(loc_vals)
                except Exception as e:
                    _logger.warning(f'Failed to update instant location on check-in: {e}')

            # Handle selfie if provided
            attachment_id = None
            if selfie_base64:
                try:
                    Attachment = request.env['ir.attachment'].sudo()
                    attachment = Attachment.create({
                        'name': f'CheckIn_Selfie_{attendance.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg',
                        'type': 'binary',
                        'datas': selfie_base64,
                        'res_model': 'hr.attendance',
                        'res_id': attendance.id,
                        'mimetype': 'image/jpeg'
                    })
                    attendance.write({'x_checkin_selfie_id': attachment.id})
                    attachment_id = attachment.id
                except Exception as e:
                    _logger.warning(f'Failed to save selfie: {str(e)}')
                    # Continue without selfie - not critical

            # Handle additional gallery images (optional)
            if gallery_images:
                try:
                    Attachment = request.env['ir.attachment'].sudo()
                    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    emp_id = hr_employee.id
                    analytic_id = analytic_account.id if analytic_account else 0
                    serial = 1
                    for img_b64 in gallery_images:
                        if not img_b64:
                            continue
                        name = f'checkin-{emp_id}-{analytic_id}-{now_str}-{serial}.jpg'
                        Attachment.create({
                            'name': name,
                            'type': 'binary',
                            'datas': img_b64,
                            'res_model': 'hr.attendance',
                            'res_id': attendance.id,
                            'mimetype': 'image/jpeg'
                        })
                        serial += 1
                except Exception as e:
                    _logger.warning(f'Failed to save check-in gallery images: {str(e)}')

            _send_manager_attendance_notification(
                employee_app=employee_app,
                hr_employee=hr_employee,
                event='check_in',
                attendance=attendance,
                analytic_account=analytic_account,
                note=checkin_note,
            )
            
            return response_helper.success_response({
                'attendance_id': attendance.id,
                'check_in': attendance.check_in.isoformat(),
                'analytic_account': {
                    'id': analytic_account.id,
                    'name': analytic_account.name,
                    'code': analytic_account.code or ''
                },
                'gps': {
                    'lat': gps_lat,
                    'lng': gps_lng,
                    'accuracy': gps_accuracy,
                    'address': gps_address
                },
                'selfie_saved': bool(attachment_id),
                'fleet_trip_id': fleet_trip.id if fleet_trip else None
            }, message='Checked in successfully')
            
        except ValidationError as e:
            _logger.warning(f'Validation error in check_in: {str(e)}')
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in check_in endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred during check-in')
    
    
    @http.route('/api/odoo-attendance/attendance/check-out', type='http', auth='public', methods=['POST'], csrf=False, cors='*')
    def check_out(self, **kwargs):
        """
        Update attendance with check-out time and GPS.
        
        POST /api/odoo-attendance/attendance/check-out
        Authorization: Bearer <access_token>
        
        Request body:
        {
            "gps_lat": 30.0445,
            "gps_lng": 31.2358,
            "gps_accuracy": 10.2,
            "gps_address": "124 Main St, Cairo, Egypt",
            "selfie_base64": "iVBORw0KGgoAAAANS..."  // optional
        }
        
        Response:
        {
            "success": true,
            "data": {
                "attendance_id": 501,
                "check_out": "2026-01-05T17:30:00",
                "worked_hours": 8.5
            }
        }
        """
        try:
            checkout_note = ''

            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            # Authenticate
            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')
            
            employee_app, hr_employee = auth_result
            
            # Parse request body
            try:
                data = json.loads(request.httprequest.data)
            except:
                return response_helper.validation_error_response('Invalid JSON in request body')
            
            gps_lat = data.get('gps_lat', 0.0)
            gps_lng = data.get('gps_lng', 0.0)
            gps_accuracy = data.get('gps_accuracy', 0.0)
            gps_address = data.get('gps_address', '')
            selfie_base64 = data.get('selfie_base64')
            gallery_images = data.get('gallery_images') or [] # <-- Added this line
            checkout_note = (data.get('note') or '').strip()

            if not checkout_note:
                return response_helper.validation_error_response('Check-out note is required.')

            if not isinstance(gallery_images, list):
                return response_helper.validation_error_response('gallery_images must be a list.')
            
            # Find open attendance
            Attendance = request.env['hr.attendance'].sudo()
            open_attendance = Attendance.search([
                ('employee_id', '=', hr_employee.id),
                ('check_out', '=', False)
            ], limit=1)
            
            if not open_attendance:
                return response_helper.validation_error_response(
                    'No open attendance found. Please check in first.'
                )

            analytic_account = open_attendance.x_analytic_account_id

            is_driver = bool(employee_app.is_driver)
            end_kilometrage = None
            fleet_trip = None
            if is_driver:
                if not hr_employee.user_id:
                    return response_helper.validation_error_response(
                        'Driver must be linked to a user account.'
                    )
                end_kilometrage = _parse_float(
                    data.get('kilometrage') if 'kilometrage' in data else data.get('end_kilometrage'),
                    'Kilometrage'
                )
                if end_kilometrage is None:
                    return response_helper.validation_error_response(
                        'Kilometrage is required for drivers.'
                    )
                FleetTrip = request.env['odoo.attendance.fleet.trip'].sudo()
                fleet_trip = FleetTrip.search([
                    ('driver_user_id', '=', hr_employee.user_id.id),
                    ('state', '=', 'in_progress'),
                    ('trip_end_date_time', '=', False)
                ], limit=1, order='trip_start_date_time desc')
                if not fleet_trip:
                    return response_helper.validation_error_response(
                        'No open trip found for this driver.'
                    )

            # Selfie policy: employee or project can require a selfie
            employee_requires_selfie = (employee_app.selfie_policy_checkout or 'optional') == 'required'
            project_requires_selfie = (analytic_account.x_selfie_policy_checkout or 'optional') == 'required' if analytic_account else False
            if (employee_requires_selfie or project_requires_selfie) and not selfie_base64:
                return response_helper.validation_error_response(
                    'please take selfie and try again'
                )
            
            # Geofence validation: if radius set (>0), require GPS and enforce distance (check-out)
            locations = get_geofence_locations(analytic_account) if analytic_account else []
            geofence_exempt = _is_geofence_exempt(analytic_account, hr_employee)

            # Skip geofence unless enabled and locations are configured
            if analytic_account and analytic_account.x_enable_geofence and locations and not geofence_exempt:
                if gps_lat is None or gps_lng is None:
                    return response_helper.validation_error_response(
                        'GPS coordinates are required for this analytic account.'
                    )

                within_radius = False
                for lat_cfg, lng_cfg, radius in locations:
                    distance_km = haversine_km(
                        lat_cfg,
                        lng_cfg,
                        float(gps_lat),
                        float(gps_lng),
                    )
                    if distance_km <= radius:
                        within_radius = True
                        break
                if not within_radius:
                    _logger.info(
                        'Check-out geofence rejected: attendance_id=%s analytic_account_id=%s',
                        open_attendance.id,
                        analytic_account.id if analytic_account else None,
                    )
                    return response_helper.forbidden_response('You are not near the project location.')
            
            # Update with check-out data
            from odoo import fields
            now = fields.Datetime.now()
            update_vals = {
                'check_out': now,
                'x_checkout_gps_lat': gps_lat,
                'x_checkout_gps_lng': gps_lng,
                'x_checkout_gps_accuracy': gps_accuracy,
                'x_checkout_gps_address': gps_address,
                'x_checkout_note': checkout_note,
            }
            if is_driver:
                update_vals.update({
                    'x_end_kilometrage': end_kilometrage,
                })
                if fleet_trip:
                    update_vals.update({
                        'x_vehicle_id': fleet_trip.vehicle_id.id,
                        'x_fleet_trip_id': fleet_trip.id,
                    })
            
            open_attendance.write(update_vals)

            if is_driver and fleet_trip:
                end_location = _format_google_maps_location(gps_address, gps_lat, gps_lng)
                fleet_trip.write({
                    'trip_end_date_time': now,
                    'end_kilometrage': end_kilometrage,
                    'end_google_maps_location': end_location,
                    'state': 'completed',
                })
                if end_kilometrage is not None:
                    try:
                        fleet_trip.vehicle_id.sudo().write({
                            'current_kilometrage': end_kilometrage
                        })
                    except Exception as e:
                        _logger.warning(f'Failed to update vehicle kilometrage: {e}')
            elif is_driver and end_kilometrage is not None and open_attendance.x_vehicle_id:
                # Fallback: ensure vehicle current kilometrage is updated even if no fleet trip.
                try:
                    open_attendance.x_vehicle_id.sudo().write({
                        'current_kilometrage': end_kilometrage
                    })
                except Exception as e:
                    _logger.warning(f'Failed to update vehicle kilometrage (fallback): {e}')
            
            # Handle selfie if provided
            if selfie_base64:
                try:
                    Attachment = request.env['ir.attachment'].sudo()
                    attachment = Attachment.create({
                        'name': f'CheckOut_Selfie_{open_attendance.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg',
                        'type': 'binary',
                        'datas': selfie_base64,
                        'res_model': 'hr.attendance',
                        'res_id': open_attendance.id,
                        'mimetype': 'image/jpeg'
                    })
                    open_attendance.write({'x_checkout_selfie_id': attachment.id})
                except Exception as e:
                    _logger.warning(f'Failed to save checkout selfie: {str(e)}')

            # Handle additional gallery images (optional)
            if gallery_images:
                try:
                    Attachment = request.env['ir.attachment'].sudo()
                    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    emp_id = hr_employee.id
                    analytic_id = analytic_account.id if analytic_account else 0
                    serial = 1
                    for img_b64 in gallery_images:
                        if not img_b64:
                            continue
                        name = f'{emp_id}-{analytic_id}-{now_str}-{serial}.jpg'
                        Attachment.create({
                            'name': name,
                            'type': 'binary',
                            'datas': img_b64,
                            'res_model': 'hr.attendance',
                            'res_id': open_attendance.id,
                            'mimetype': 'image/jpeg'
                        })
                        serial += 1
                except Exception as e:
                    _logger.warning(f'Failed to save checkout gallery images: {str(e)}')

            _send_manager_attendance_notification(
                employee_app=employee_app,
                hr_employee=hr_employee,
                event='check_out',
                attendance=open_attendance,
                analytic_account=open_attendance.x_analytic_account_id,
                note=checkout_note,
            )
            
            return response_helper.success_response({
                'attendance_id': open_attendance.id,
                'check_in': open_attendance.check_in.isoformat(),
                'check_out': open_attendance.check_out.isoformat(),
                'worked_hours': round(open_attendance.worked_hours, 2),
                'analytic_account': {
                    'id': open_attendance.x_analytic_account_id.id,
                    'name': open_attendance.x_analytic_account_id.name
                } if open_attendance.x_analytic_account_id else None,
                'fleet_trip_id': fleet_trip.id if fleet_trip else None
            }, message='Checked out successfully')
            
        except ValidationError as e:
            _logger.warning(f'Validation error in check_out: {str(e)}')
            return response_helper.validation_error_response(str(e))
        except Exception as e:
            _logger.exception(f'Error in check_out endpoint: {str(e)}')
            import traceback
            error_message = f'An error occurred during check-out: {str(e)}\n{traceback.format_exc()}'
            return response_helper.server_error_response(error_message)

    @http.route(
        '/odoo_attendance_app/attendance/<int:attendance_id>/checkout_photos.zip',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def download_checkout_photos_zip(self, attendance_id, **kwargs):
        attendance = request.env['hr.attendance'].browse(attendance_id).exists()
        if not attendance:
            return request.not_found()

        attendance.check_access_rights('read')
        attendance.check_access_rule('read')

        emp_id = attendance.employee_id.id or 0
        analytic_id = attendance.x_analytic_account_id.id or 0
        prefix = f'{emp_id}-{analytic_id}-'

        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.attendance'),
            ('res_id', '=', attendance.id),
            ('name', '=ilike', f'{prefix}%'),
        ], order='create_date asc')

        # Keep only those matching our serial naming scheme
        attachments = attachments.filtered(
            lambda a: attendance._is_checkout_gallery_attachment_name(a.name, emp_id, analytic_id)
        )
        if not attachments:
            return request.not_found()

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for attachment in attachments:
                datas_b64 = attachment.with_context(bin_size=False).datas
                if not datas_b64:
                    continue
                try:
                    content = base64.b64decode(datas_b64)
                except Exception:
                    continue
                filename = attachment.name or f'{attendance.id}-{attachment.id}.jpg'
                zf.writestr(filename, content)

        buffer.seek(0)
        zip_name = f'checkout_photos_attendance_{attendance.id}.zip'
        headers = [
            ('Content-Type', 'application/zip'),
            ('Content-Disposition', f'attachment; filename=\"{zip_name}\"'),
        ]
        return request.make_response(buffer.getvalue(), headers=headers)

    @http.route(
        '/odoo_attendance_app/attendance/<int:attendance_id>/checkin_photos.zip',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def download_checkin_photos_zip(self, attendance_id, **kwargs):
        attendance = request.env['hr.attendance'].browse(attendance_id).exists()
        if not attendance:
            return request.not_found()

        attendance.check_access_rights('read')
        attendance.check_access_rule('read')

        emp_id = attendance.employee_id.id or 0
        analytic_id = attendance.x_analytic_account_id.id or 0
        prefix = f'checkin-{emp_id}-{analytic_id}-'

        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.attendance'),
            ('res_id', '=', attendance.id),
            ('name', '=ilike', f'{prefix}%'),
        ], order='create_date asc')

        attachments = attachments.filtered(
            lambda a: attendance._is_checkin_gallery_attachment_name(a.name, emp_id, analytic_id)
        )
        if not attachments:
            return request.not_found()

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for attachment in attachments:
                datas_b64 = attachment.with_context(bin_size=False).datas
                if not datas_b64:
                    continue
                try:
                    content = base64.b64decode(datas_b64)
                except Exception:
                    continue
                filename = attachment.name or f'{attendance.id}-{attachment.id}.jpg'
                zf.writestr(filename, content)

        buffer.seek(0)
        zip_name = f'checkin_photos_attendance_{attendance.id}.zip'
        headers = [
            ('Content-Type', 'application/zip'),
            ('Content-Disposition', f'attachment; filename=\"{zip_name}\"'),
        ]
        return request.make_response(buffer.getvalue(), headers=headers)
    
    
    @http.route('/api/odoo-attendance/attendance/history', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def history(self, **kwargs):
        """
        Get attendance history with optional date filtering.
        
        GET /api/odoo-attendance/attendance/history?from=2026-01-01&to=2026-01-31&limit=50
        Authorization: Bearer <access_token>
        
        Query parameters:
        - from: start date (YYYY-MM-DD) optional
        - to: end date (YYYY-MM-DD) optional
        - limit: max results (default 50)
        
        Response:
        {
            "success": true,
            "data": [
                {
                    "id": 501,
                    "check_in": "2026-01-05T09:00:00",
                    "check_out": "2026-01-05T17:30:00",
                    "worked_hours": 8.5,
                    "analytic_account": {...},
                    "gps_checkin": {...},
                    "gps_checkout": {...}
                },
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
            from_date = request.params.get('from')
            to_date = request.params.get('to')
            limit = int(request.params.get('limit', 50))
            
            # Build domain
            domain = [('employee_id', '=', hr_employee.id)]
            
            if from_date:
                try:
                    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
                    domain.append(('check_in', '>=', from_dt))
                except:
                    return response_helper.validation_error_response('Invalid from date format. Use YYYY-MM-DD')
            
            if to_date:
                try:
                    to_dt = datetime.strptime(to_date, '%Y-%m-%d')
                    # Add one day to include the entire end date
                    from datetime import timedelta
                    to_dt = to_dt + timedelta(days=1)
                    domain.append(('check_in', '<', to_dt))
                except:
                    return response_helper.validation_error_response('Invalid to date format. Use YYYY-MM-DD')
            
            # Search attendances
            Attendance = request.env['hr.attendance'].sudo()
            attendances = Attendance.search(domain, limit=limit, order='check_in desc')
            
            results = []
            for att in attendances:
                analytic_display = None
                if att.x_analytic_account_id:
                    code = (att.x_analytic_account_id.code or '').strip()
                    name = (att.x_analytic_account_id.name or '').strip()
                    analytic_display = f'[{code}] {name}' if code else name
                results.append({
                    'id': att.id,
                    'check_in': att.check_in.isoformat() if att.check_in else None,
                    'check_out': att.check_out.isoformat() if att.check_out else None,
                    'worked_hours': round(att.worked_hours, 2),
                    'analytic_account_id': att.x_analytic_account_id.id if att.x_analytic_account_id else None,
                    'analytic_account_display_name': analytic_display,
                    'analytic_account': {
                        'id': att.x_analytic_account_id.id,
                        'name': att.x_analytic_account_id.name,
                        'code': att.x_analytic_account_id.code or '',
                        'display_name': analytic_display,
                    } if att.x_analytic_account_id else None,
                    'gps_checkin': {
                        'lat': att.x_checkin_gps_lat,
                        'lng': att.x_checkin_gps_lng,
                        'accuracy': att.x_checkin_gps_accuracy,
                        'address': att.x_checkin_gps_address
                    } if att.x_checkin_gps_lat else None,
                    'gps_checkout': {
                        'lat': att.x_checkout_gps_lat,
                        'lng': att.x_checkout_gps_lng,
                        'accuracy': att.x_checkout_gps_accuracy,
                        'address': att.x_checkout_gps_address
                    } if att.x_checkout_gps_lat else None,
                    'has_checkin_selfie': bool(att.x_checkin_selfie_id),
                    'has_checkout_selfie': bool(att.x_checkout_selfie_id)
                })
            
            return response_helper.success_response(results)
            
        except Exception as e:
            _logger.exception(f'Error in history endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')

    @http.route('/api/odoo-attendance/attendance/today-total', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def today_total(self, **kwargs):
        """
        Get today's total worked time (in seconds) for the authenticated employee.

        This is used by the mobile app to display a live counter of today's worked time.

        GET /api/odoo-attendance/attendance/today-total?tz_offset_minutes=120
        Authorization: Bearer <access_token>
        """
        try:
            sub_resp = require_active_subscription()
            if sub_resp:
                return sub_resp

            auth_result = authenticate_request()
            if not auth_result:
                return response_helper.unauthorized_response('Invalid or missing authentication token')

            _employee_app, hr_employee = auth_result

            now_utc = fields.Datetime.now()

            # Optional: allow the app to define "today" based on the device timezone offset.
            # tz_offset_minutes is minutes east of UTC (e.g., Cairo is +120).
            tz_offset_minutes_raw = request.params.get('tz_offset_minutes')
            tz_offset_minutes = 0
            if tz_offset_minutes_raw not in (None, ''):
                try:
                    tz_offset_minutes = int(tz_offset_minutes_raw)
                except Exception:
                    return response_helper.validation_error_response('Invalid tz_offset_minutes. Must be an integer.')

            from datetime import timedelta
            offset = timedelta(minutes=tz_offset_minutes)
            local_now = now_utc + offset
            local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            local_end = local_start + timedelta(days=1)
            start_utc = local_start - offset
            end_utc = local_end - offset

            Attendance = request.env['hr.attendance'].sudo()
            attendances = Attendance.search(
                [
                    ('employee_id', '=', hr_employee.id),
                    ('check_in', '<', end_utc),
                    '|',
                    ('check_out', '=', False),
                    ('check_out', '>', start_utc),
                ],
                order='check_in asc',
            )

            total_seconds = 0
            for att in attendances:
                if not att.check_in:
                    continue
                seg_start = max(att.check_in, start_utc)
                seg_end = att.check_out or now_utc
                seg_end = min(seg_end, end_utc)
                if seg_end > seg_start:
                    total_seconds += int((seg_end - seg_start).total_seconds())

            return response_helper.success_response(
                {
                    'date_start_utc': start_utc.isoformat(),
                    'date_end_utc': end_utc.isoformat(),
                    'total_seconds': total_seconds,
                }
            )
        except Exception as e:
            _logger.exception(f'Error in today-total endpoint: {str(e)}')
            return response_helper.server_error_response('An error occurred')



