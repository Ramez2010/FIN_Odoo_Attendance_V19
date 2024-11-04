
from ast import literal_eval
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime
from odoo.exceptions import UserError
import random
import json
import re
from .fcmAPI import FCMAPI
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
import logging
from odoo.addons.mobikul_odoo_attendance.tools.constdata import _get_image_url,_easy_date
_logger = logging.getLogger(__name__)

class FcmAttendanceDevices(models.Model):
    _name = 'fcm.attendance.devices'
    _description = 'All Registered Devices on FCM for Push Notifications.'
    _order = 'write_date desc'

    def name_get(self):
        res = []
        for record in self:
            name = record.customer_id and record.customer_id.name or ''
            res.append((record.id, "%s(DeviceId:%s)" % (name, record.device_id)))
        return res

    def remove_all_devices(self,customer_id):
        '''
            Function called in case of reset password to remove all cutomer from registered fcm
            In short logout from all device
        '''
        allDevices = self.search([("customer_id","=",customer_id)])
        if allDevices!=0:
            for device in allDevices:
                device.sudo().write({'token': device.token, 'customer_id': False})

    name = fields.Char('Name')
    token = fields.Text('FCM Registration ID', readonly=True)
    device_id = fields.Char('Device Id', readonly=True)
    customer_id = fields.Many2one('res.partner', string="Customer", readonly=True, index=True)
    active = fields.Boolean(default=True, readonly=True)
    description = fields.Text('Description', readonly=True)

class FcmRegisteredTopics(models.Model):
    _name = 'fcm.attendance.topics'
    _description = 'All Registered Topics for Push Notifications.'

    name = fields.Char('Topic Name', required=True)


class MobikulAtdNotificationTemplate(models.Model):
    _name = 'mobikul.attendance.notification.template'
    _description = 'Mobikul Attendance Notification Templates'
    _order = "name"

    def _addMe(self, data):
        self.env["mobikul.attendance.messages"].sudo().create(data)
        return True

    def _get_key(self):
        mobikul = self.env['mobikul.attendance'].sudo().search([], limit=1)
        return mobikul and mobikul.fcm_api_key or ""

    @api.model
    def _pushMe(self, key, payload_data, data=False):
        status = True
        summary = ""
        try:
            push_service = FCMAPI(api_key=key)
            summary = push_service.send([payload_data])
            if data:
                self._addMe(data)
        except Exception as e:
            status = False
            summary = "Error: %r" % e
        return [status, summary]

    @api.model
    def _send(self, to_data, customer_id=False, max_limit=20):
        """
        to_data = dict(to or registration_ids)
        """
        if type(to_data) != dict:
            return False
        if not to_data.get("to", False) and not to_data.get("registration_ids", False):
            if not customer_id:
                return False
            reg_data = self.env['fcm.attendance.devices'].sudo().search_read(
                [('customer_id', '=', customer_id)], limit=max_limit, fields=['token'])
            if not reg_data:
                return False
            to_data = {
                "registration_ids": [r['token'] for r in reg_data]
            }
        notification = dict(title=self.notification_title,
                            body=self.notification_body, sound="default")
        if self.notification_color:
            notification['color'] = self.notification_color
        if self.notification_tag:
            notification['tag'] = self.notification_tag

        fcm_payload = dict(notification=notification)
        fcm_payload.update(to_data)
        data_message = dict(type="", id="", domain="", image="", name="")
        data_message['name'] = self.notification_title
        data_message['type'] = 'none'
        data_message['image'] = _get_image_url(self._context.get(
            'base_url'), 'mobikul.attendance.notification.template', self.id, 'image', self.write_date)
        data_message['notificationId'] = random.randint(1, 99999)
        fcm_payload['data'] = data_message
        domain = [('res_model', '=', self._name),
            ('res_field', '=', 'image'),
            ('res_id', 'in', [self.id])]
        attachment = self.env['ir.attachment'].sudo().search(domain)
        if customer_id:
            data = dict(
                title=self.notification_title, body=self.notification_body, customer_id=customer_id,
                banner=attachment.datas, datatype='default'
            )
        return self._pushMe(self._get_key(), json.dumps(fcm_payload).encode('utf8'), customer_id and data or False)

    name = fields.Char('Name', required=True, translate=True)
    notification_color = fields.Char('Color', default='PURPLE')
    notification_tag = fields.Char('Tag')
    notification_title = fields.Char('Title', required=True, translate=True)
    active = fields.Boolean(default=True, copy=False)
    notification_body = fields.Text('Body', translate=True)
    image = fields.Binary('Image', attachment=True)
    device_id = fields.Many2one('fcm.attendance.devices', string='Select Device')
    total_views = fields.Integer('Total # Views', default=0, readonly=1, copy=False)
    condition = fields.Selection([
        ('login', "Employee Login"),
        ('checkin', "Employee Checkin"),
        ('checkout', "Employee Checkout"),
    ], string='Condition', required=True, default='checkin')

    def dry_run(self):
        self.ensure_one()
        to_data = dict(to=self.device_id and self.device_id.token or "")
        result = self._send(
            to_data, self.device_id and self.device_id.customer_id and self.device_id.customer_id.id or False)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_('%s(copy)') % self.name)
        return super(MobikulAtdNotificationTemplate, self).copy(default)

class MobikulAtdNotification(models.Model):
    _name = 'mobikul.attendance.notification'
    _description = 'Mobikul Attendance Push Notification'
    _order = "activation_date, name"
    _inherit = ['mobikul.attendance.notification.template']

    @api.model
    def parse_n_push(self, max_limit=20, registration_ids=None):
        to_data = dict()
        mobikul = self.env["mobikul.attendance"].sudo().search([],limit=1)
        app_lang = mobikul.default_lang and mobikul.default_lang.code or "en_US"
        if self.notification_type == 'token-auto':
            reg_data = self.env['fcm.attendance.devices'].sudo(
            ).search_read(limit=max_limit, fields=['token'])
            registration_ids = [r['token'] for r in reg_data]
        elif self.notification_type == 'token-manual':
            registration_ids = [d.token for d in self.device_ids]
        elif self.notification_type == 'topic':
            to_data['to'] = '/topics/%s' % self.topic_id.name
        else:
            return [False, "Insufficient Data"]

        if registration_ids:
            if len(registration_ids) > 1:
                to_data['registration_ids'] = registration_ids
            else:
                to_data['to'] = registration_ids[0]
        return self.with_context(lang=app_lang,lang_obj=self.env['res.lang']._lang_get(app_lang))._send(to_data)


    summary = fields.Text('Summary', readonly=True)
    activation_date = fields.Datetime('Activation Date', copy=False)
    notification_type = fields.Selection([
        ('token-auto', 'Token-Based(All Reg. Devices)'),
        ('token-manual', 'Token-Based(Selected Devices)'),
        ('topic', 'Topic-Based'),
    ],
        string='Type', required=True,
        default='token-auto')
    topic_id = fields.Many2one('fcm.attendance.topics', string='Choose Topic')
    device_ids = fields.Many2many('fcm.attendance.devices', string='Choose Devices/Customers')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('hold', 'Hold'),
        ('error', 'Error'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'
        return True

    def action_confirm(self):
        for record in self:
            record.state = 'confirm'
        return True

    def action_draft(self):
        for record in self:
            record.state = 'draft'
        return True

    def action_hold(self):
        for record in self:
            record.state = 'hold'
        return True

    def push_now(self):
        for record in self:
            response = record.parse_n_push()
            record.state = response[0] and 'done' or 'error'
            record.summary = response[1]
        return True

    def duplicate_me(self):
        self.ensure_one()
        action = self.env.ref('mobikul_odoo_attendance.mobikul_atd_notification_action').read()[0]
        action['views'] = [(self.env.ref('mobikul_odoo_attendance.mobikul_atd_notification_view_form').id, 'form')]
        action['res_id'] = self.copy().id
        return action

class MobikulAtdNotificationMessages(models.Model):
    _name = 'mobikul.attendance.messages'
    _description = 'Mobikul Attendance Notification Messages'

    name = fields.Char('Message Name', default='/', index=True, copy=False, readonly=True)
    title = fields.Char('Title')
    subtitle = fields.Char('Subtitle')
    body = fields.Text('Body')
    icon = fields.Binary('Icon')
    banner = fields.Binary('Banner')
    is_read = fields.Boolean('Is Read', default=False, readonly=True)
    customer_id = fields.Many2one('res.partner', string="Customer", index=True)
    active = fields.Boolean(default=True, readonly=True)
    period = fields.Char('Period', compute='_compute_period')
    datatype = fields.Selection([
        ('default', 'Default'),
        ('order', 'Order')],
        string='Data Type', required=True,
        default='default',
        help="Notification Messages Data Type for your Mobikul App.")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('mobikul.attendance.messages')
        return super(MobikulAtdNotificationMessages, self).create(vals)

    def _compute_period(self):
        for i in self:
            i.period = _easy_date(i.create_date)