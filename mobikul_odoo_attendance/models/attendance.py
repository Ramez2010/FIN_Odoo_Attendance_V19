from ast import literal_eval
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import pytz
import random
import json
import re
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
import logging
_logger = logging.getLogger(__name__)


class Mobikul_Attendance(models.Model):
    _name = "mobikul.attendance"
    _description = "Mobile Attendance Model"

    def _default_language(self):
        lc = self.env['ir.default'].get('res.partner', 'lang')
        dl = self.env['res.lang'].search([('code', '=', lc)], limit=1)
        return dl.id if dl else self.env['res.lang'].search([]).ids[0]

    def _getdefaultCompany_id(self):
        comp_id = self.env['res.company'].search([], limit=1)
        return comp_id.id

    def _active_languages(self):
        return self.env['res.lang'].search([]).ids

    @api.model
    def resetPassword(self, login):
        response = {'success': False}
        try:
            if login:
                self.env['res.users'].sudo().reset_password(login)
                response['success'] = True
                response['message'] = _(
                    "An email has been sent with credentials to reset your password")
            else:
                response['message'] = _("No login provided.")
        except MailDeliveryException as me:
            response['message'] = _("Exception : %r" % me)
        except Exception as e:
            response['message'] = _("Invalid Username/Email.")
        return response

    name = fields.Char('Mobile Attendance App Title', default="Mobikul Attendance App", required=1)
    api_key = fields.Char(string='API Secret key', default="dummySecretKey", required=1)
    fcm_api_key = fields.Char(string='FCM Api key')
    default_lang = fields.Many2one('res.lang', string='Default Language', default=_default_language,
                                   help="If the selected language is loaded in the mobikul, all documents related to "
                                   "this contact will be printed in this language. If not, it will be English.")
    privacy_policy = fields.Char(string='Privacy Policy', help="Add your website privacy policy URL")
    company_id = fields.Many2one('res.company', default=_getdefaultCompany_id,
                                 help="select company id for the app")
                                 
    language_ids = fields.Many2many('res.lang', 'mobikul_atd_lang_rel',
                                    'mobikul_attendance_id', 'lang_id', 'Languages', default=_active_languages)
    
    def unlink(self):
        raise UserError(_('You cannot remove/deactivate this Configuration.'))


class HRAttendanceInherit(models.Model):
    _inherit = 'hr.attendance'

    def check_out_notifications_reminder(self):
        now = datetime.now()
        threshold_time = now - timedelta(hours=8)
        one_hour_ago = now - timedelta(hours=1)

        # Search for attendance records that match the criteria
        attendance_records = self.search([
            ('check_in', '>=', now.replace(hour=0, minute=0, second=0, microsecond=0)),
            ('check_in', '<=', threshold_time),
            ('check_out', '=', False)
        ])

        for record in attendance_records:
            # Check if a notification has already been sent in the last hour
            last_notification = self.env['mobikul.attendance.notification'].search([
                ('device_ids', 'in', record.employee_id.user_id.partner_id.id),
                ('create_date', '>=', one_hour_ago)
            ], limit=1)

            if last_notification:
                _logger.info('Notification already sent for employee %s within the last hour.', record.employee_id.name)
                continue  # Skip sending a new notification

            # Prepare to send notification
            device_id = False
            device = self.env['fcm.attendance.devices'].sudo().search([
                ('customer_id', '=', record.employee_id.user_id.partner_id.id)
            ], limit=1)

            if device:
                device_id = device.id

            self.create_departure_notification(device_id)

    def create_departure_notification(self, device_id):
        vals = {
            'name': 'Reminder To Checkout',
            'notification_title': 'Reminder To Checkout',
            'notification_type': 'token-manual',
            'notification_body': "Please don't forget to checkout if you ended your work.",
        }
        if device_id:
            vals['device_ids'] = [(6, 0, [device_id])]

        record = self.env['mobikul.attendance.notification'].create(vals)

        try:
            # Set the Arabic translation
            record.with_context(lang='ar_001').name = 'تذكير بتسجيل الخروج'
            record.with_context(lang='ar_001').notification_title = 'تذكير بتسجيل الخروج'
            record.with_context(lang='ar_001').notification_body = 'يرجي تسجيل بصمة الخروج اذا انهيت العمل.'
            record.action_confirm()
            record.push_now()
        except Exception as e:
            _logger.error('Failed to send notification: %s', e)