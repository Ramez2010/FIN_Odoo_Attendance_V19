# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import logging
import werkzeug
import json
from jwt.exceptions import DecodeError
from ast import literal_eval
from functools import wraps
from base64 import b64decode
from odoo import http, _,fields,tools
from odoo.fields import Datetime, Date, Selection
from odoo.addons.mobikul_odoo_attendance.tools.jwt_token import jwt_encode, jwt_decode
from odoo.addons.mobikul_odoo_attendance.tools.constdata import mobikulFormatTimeZone,fcmDeviceCheck,_pushNotification, _tokenUpdate,getDefaultData, _languageData, _get_image_url,mobikul_display_address
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools import format_datetime

_logger = logging.getLogger(__name__)


def get_jwt_token(secret, *args, algorithm = "HS256", **kwargs):
    payload = {
      "partner_id": args[0],
      "user_id": args[1]
    }
    token = jwt_encode(payload, secret, algorithm)
    return token


class xml(object):

    @staticmethod
    def _encode_content(data):
        # .replace('&', '&amp;')
        return data.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    @classmethod
    def dumps(cls, apiName, obj):
        _logger.warning("%r : %r" % (apiName, obj))
        if isinstance(obj, dict):
            return "".join("<%s>%s</%s>" % (key, cls.dumps(apiName, obj[key]), key) for key in obj)
        elif isinstance(obj, list):
            return "".join("<%s>%s</%s>" % ("I%s" % index, cls.dumps(apiName, element), "I%s" % index) for index, element in enumerate(obj))
        else:
            return "%s" % (xml._encode_content(obj.__str__()))

    @staticmethod
    def loads(string):
        def _node_to_dict(node):
            if node.text:
                return node.text
            else:
                return {child.tag: _node_to_dict(child) for child in node}
        root = ET.fromstring(string)
        return {root.tag: _node_to_dict(root)}


class MobikulAttendanceAPI(http.Controller):


    def _wrap2xml(self, apiName, data):
        resp_xml = "<?xml version='1.0' encoding='UTF-8'?>"
        resp_xml += '<odoo xmlns:xlink="http://www.w3.org/1999/xlink">'
        resp_xml += "<%s>" % apiName
        resp_xml += xml.dumps(apiName, data)
        resp_xml += "</%s>" % apiName
        resp_xml += '</odoo>'
        return resp_xml


    def _response(self, apiName, response, ctype='json'):
        if response.get("context"):
            response.pop("context")
        if 'local' in response:
            response.pop("local")
        if ctype == 'json':
            mime = 'application/json; charset=utf-8'
            body = json.dumps(response)
        else:
            mime = 'text/xml'
            body = self._wrap2xml(apiName, response)
        headers = [
            ('Content-Type', mime),
            ('Content-Length', len(body))
        ]
        return werkzeug.wrappers.Response(body, headers=headers)


    def __decorateMe(method):
        @wraps(method)
        def wrapped(self, *args, **kwargs):
            _logger.info("======kwargs====%r",kwargs)
            self.authenticate = kwargs.get('authenticate', False)

            self.authorize = kwargs.get('authorize', False)
            self._mData = request.httprequest.data and json.loads(
                request.httprequest.data.decode('utf-8')) or {}
            self._mAuth = request.httprequest.headers.get('Authorization')
            if not self.authorize and self._mAuth:
                self.authorize = True
            self.base_url = request.httprequest.host_url
            self._lcred = {}
            self._mLang = request.httprequest.headers.get("lang") or None
            if request.httprequest.headers.get("Login"):
                # try:
                if True:
                    self._lcred = literal_eval(
                        b64decode(request.httprequest.headers["Login"]).decode('utf-8'))
                    if not self.authorize and not self.authenticate:
                        self.authenticate = True
                # except Exception as e:
                #     self._lcred = {"login": None, "pwd": None}
            # TODO Social login implementation is on hold, it could be done in second phase of the app or the module
            return method(self, *args, **kwargs)
        return wrapped


    def __authenticate(self):
        """
        Authenticate user through the login header provided in the header
        """
        response = {'success': False, 'responseCode': 400, 'message': _('Unknown Error !!!')}
        user = False
        credentials = self._lcred
        if not isinstance(credentials, dict):
            response['message'] = _('Data is not in Dictionary format !!!')
            return response
        # TODO Social login implementation is on hold, it could be done in second phase of the app or the module
        if not all(k in credentials for k in ('login', 'pwd')):
            response['message'] = _('Insufficient data to authenticate !!!')
            return response
        # try:
        if True:
            user = request.env['res.users'].sudo().search([('login', '=', credentials['login'])])
            if user:
                user.with_user(user)._check_credentials(credentials['pwd'],{'interactive':True})
                response['success'] = True
                response['responseCode'] = 200
                response['user'] = user
                response['message'] = 'Success'
                response['authorizeToken'] = get_jwt_token(self.secret_key, user.partner_id.id, user.id)
                # .decode('utf-8')
            else:
                response['responseCode'] = 400
                response['message'] = _("Invalid password/email address.")
        # except Exception as e:
        #     user = False
        #     response['responseCode'] = 400
        #     response['message'] = _("Login Failed.")
        #     response['details'] = "%r" % e
        return response


    def __authorize(self):
        """
        Authorize user through the provided jwt token
        """
        response = {'success': False, 'responseCode': 400, 'message': _('Unknown Error !!!')}
        user = False
        secret = self.secret_key
        token = self._mAuth
        if token:
            token = token.split(" ")[1]
        try:
            payload = jwt_decode(token, secret, 'HS256')
            USER = request.env['res.users'].sudo()
            if payload:
                user = USER.browse(payload['user_id'])
                if user:
                    response['success'] = True
                    response['responseCode'] = 200
                    response['user'] = user
                    response['message'] = _('Authorized successfully!!!')
        except DecodeError as de:
            _logger.info("this is issue %r",de)
            response['message'] = _('Invalid token')
            response['details'] = _("%s".format(de.args[0]))
        return response


    @__decorateMe
    def __auth(self, *args, **kwargs):
        """
        Method to handle the user authentication and authorization
        """
        result = {'success': True, 'responseCode': 200}

        #----------- Authentication Part Starts here ---------#
        #This is use here as we need mobikul Obj in all case
        mobikul_attendance = request.env['mobikul.attendance'].sudo().search([], limit=1)
        self.secret_key = mobikul_attendance.api_key
        if self.authorize:
            result.update(self.__authorize())

        if self.authenticate:
            result.update(self.__authenticate())
        #----------- Ends here ---------#

        #----- Getting some defalut data/context for all the API's-----#
        user = result.pop('user', '')
        app_lang = mobikul_attendance.default_lang and mobikul_attendance.default_lang.code or "en_US"
        company_id = mobikul_attendance.company_id.id or 1
        result['context'] = {
            "base_url": self.base_url,
            'lang': app_lang,
            'lang_obj': request.env['res.lang']._lang_get(app_lang),
            'company_id':company_id,
            "mobikulAttObj":mobikul_attendance
        }

        #---- Data/Context which is only added when we get user from Authentication part ---#
        if user:
            #----- Security Device Check  -----#
            result.update(fcmDeviceCheck(self,user,kwargs.get("notCheckFcm")))
            #---- Context update----#
            if result['success']:
                result["context"].update({
                    'uid': user.id,
                    'partner_id': user.partner_id.id,
                    "user": user,
                })
        result.update(getDefaultData(self,mobikul_attendance))
        return result

    def _get_user_data(self,context,empfull_details = False,private_info=False):
        """
            empfull_details: True for all data of employess,
            private_info: True to return all private data of user
            Return: Dic of the employee details
        """
        userObj = context.get('user')
        company = request.env['res.company'].browse([context.get('company_id')])
        employeeObj = userObj.with_company(company).employee_id
        response = {"success":False,"message":_("Employee Not Found"),"responseCode":400}
        if employeeObj.id:
            context["employeeObj"] = employeeObj
            temp = {}
            temp.update({
                "name":employeeObj.name or "",
                "workMobile":employeeObj.mobile_phone or "",
                "workPhone":employeeObj.work_phone or "",
                "workEmail":employeeObj.work_email or "",
                "jobTitle":employeeObj.job_title or "",
                "customerProfileImage":_get_image_url(self.base_url,'hr.employee',employeeObj.id,'image_1920',employeeObj.write_date)
            })
            if empfull_details:
                temp.update({
                    "departmentId":employeeObj.department_id and employeeObj.department_id.name or "",
                    "categoryIds":employeeObj.category_ids.mapped('name'),
                    "workLocation":employeeObj.work_location_id and employeeObj.work_location_id.name or "",
                    "workAddress":mobikul_display_address(employeeObj.address_id._display_address(), employeeObj.address_id.name),
                    "worrkingHours":employeeObj.resource_calendar_id and employeeObj.resource_calendar_id.name or "",
                    "timezone":employeeObj.tz
                })
            if private_info:
                response['user_private_info'] = {
                    'address':mobikul_display_address(employeeObj.address_home_id._display_address(), employeeObj.address_home_id.name),
                    'phone':employeeObj.phone or "",
                    'email':employeeObj.private_email or "",
                    'kmFromHome':employeeObj.km_home_work or 0,
                }
            response.update({
                'employeeDetails':temp or {},
                "success": True,
                "responseCode":200,
                "message": _('Login Successfully')
            })
        return response

    def _get_attendance_state(self,context):
        """
            Provide the updated steat and other attendance detail of employee
        """
        employeeObj = context.get('employeeObj')

        '''
            This indicates that the last checkin time and checkout time belongs to current date
            If true means its employe checking and checkout data is for today else its from previous day
        '''
        checkoutToday = True
        response = {}
        now = fields.Datetime.now().strftime('%Y-%m-%d')

        if employeeObj.attendance_state == "checked_out":
            now = fields.Datetime.now().strftime('%Y-%m-%d')
            lastCheckout = employeeObj.last_check_out and employeeObj.last_check_out.strftime('%Y-%m-%d') or ""
            if lastCheckout and now > lastCheckout:
                checkoutToday = False
        response.update({
            'attendanceState':employeeObj.attendance_state or "",
            'presentState':employeeObj.hr_presence_state or "",
            'hoursToday':employeeObj.hours_today or 0.0,
            'workHours':employeeObj.last_attendance_id.worked_hours,
            'lastCheckinTime': Datetime.to_string(mobikulFormatTimeZone(employeeObj.last_check_in,employeeObj.tz)) or "",
            'lastCheckoutTime': Datetime.to_string(mobikulFormatTimeZone(employeeObj.last_check_out,employeeObj.tz)) or "",
        })
        if not checkoutToday:
            response.update({
                'lastCheckinTime': "",
                'lastCheckoutTime': ""
            })
        return response


    @http.route('/v2/mobikul/odoo_attendance/splash_page', type='http', auth="none", methods=['GET'])
    def splash_page(self):
        response = self.__auth()
        if response.get('success'):
            response.update({'message':_("Splash Page")})
            response.update(_languageData(response.get("context")))
        return self._response('SPLASH_PAGE', response)

    @http.route('/v2/mobikul/odoo_attendance/login', type='http', auth="none", methods=['POST'],csrf = False)
    def login_page(self):
        response = self.__auth(authenticate=True,notCheckFcm = True)
        if response.get('success'):
            context = response.get('context')
            if context.get('uid'):
                response.update(self._get_user_data(context))
                _logger.info("=========response=====%r",response)
                if response.get('success'):
                    _tokenUpdate(self,context.get('partner_id'))
                    _pushNotification(self._mData.get("fcmToken", ""), condition='login',
                                    customer_id=context.get('partner_id'))
                else:
                    response.pop("authorizeToken")
        return self._response('Login', response)

    @http.route('/v2/mobikul/odoo_attendance/logout', type='http', auth="none", methods=['POST'], csrf = False)
    def logout_page(self):
        response = self.__auth(authorize=True,notCheckFcm = True)
        if response.get('success'):
            context = response.get('context')
            if context.get('uid'):
                _tokenUpdate(self)
        return self._response('Login', response)

    @http.route('/v2/mobikul/odoo_attendance/homepage', type='http', auth="none", methods=['GET'])
    def homepage(self):
        response = self.__auth(authorize=True)
        if response.get('success'):
            context = response.get('context')
            if context.get('uid'):
                response.update(self._get_user_data(context))
                if response.get('success'):
                    response.update(self._get_attendance_state(context))
        return self._response('Homepage', response)

    @http.route('/v2/mobikul/odoo_attendance/profile', type='http', auth="none", methods=['GET'])
    def profile(self):
        response = self.__auth(authorize=True)
        if response.get('success'):
            context = response.get('context')
            if context.get('uid'):
                '''We can trigger this private infor part according to front end as well with some key'''
                response.update(self._get_user_data(context,empfull_details=True,private_info=True))
        return self._response('Profile', response)

    @http.route('/v2/mobikul/odoo_attendance/changeState', type='http', auth="none", methods=['PUT'],csrf = False)
    def checkin_checkout(self, **kwargs):
        """
        Api To Chnage the state of the user from checkin -> checkout and vice versa
        """
        response = self.__auth(authorize=True)

        # geolocation_tracking = True
        latitude = self._mData.get('latitude')
        _logger.info("this is the latitude comes from mobile app", latitude)
        longitude = self._mData.get('longitude')
        _logger.info("this is the longitude comes from mobile app", longitude)
        message = self._mData.get('message')
        _logger.info("this is the message comes from mobile app", message)

        if not latitude:
            latitude = False
        if not longitude:
            longitude = False
        if not message:
            message = False

        # Analytic Account
        analytic_account_id = False
        if self._mData.get('analytic_account_id'):
            analytic_account_id = self._mData.get('analytic_account_id')

        data_list = [message, latitude, longitude]


        response['latitude'] = latitude
        response['longitude'] = longitude

        if analytic_account_id:
            data_list.append(analytic_account_id)
            response["analytic_account_id"] = analytic_account_id

        if response.get('success'):
            context = response.get('context')
            if context.get('uid'):
                response.update(self._get_user_data(context))
                if response.get('success'):
                    try:
                        employeeObj = context.get("employeeObj")
                        employeeObj.sh_attendance_action_change(data_list)
                        response.update(self._get_attendance_state(context))
                        if response.get('attendanceState') == "checked_in":
                            response['message'] = "Welcome %s!" % (response.get("employeeDetails")['name'])
                            _pushNotification(self._mData.get("fcmToken", ""), condition='checkin',
                                   customer_id=context.get('partner_id'))
                        else:
                            response['message'] = "Goodbye %s!" % (response.get("employeeDetails")['name'])
                            _pushNotification(self._mData.get("fcmToken", ""), condition='checkout',
                                   customer_id=context.get('partner_id'))
                    except Exception as e:
                        response['success'] = False
                        response['message'] = _("%s".format(e.args[0]))
                        response['responseCode'] = 400
        return self._response('Checkin Checkout', response)

    @http.route('/v2/mobikul/odoo_attendance/history', type='http', auth="none", methods=['GET'])
    def history(self,date_begin=None, date_end=None):
        """
        Return the list of all attendance of employee
        """
        response = self.__auth(authorize=True)
        if response.get('success'):
            context = response.get('context')
            if context.get('uid'):
                response.update(self._get_user_data(context))
                if response.get('success'):
                    #TODO to get default limit from view
                    limit = self._mData.get('limit') or 10
                    offset = self._mData.get('offset') or 0
                    step = offset+limit
                    employeeObj = context.get("employeeObj")
                    hrAttendance = request.env['hr.attendance'].sudo()
                    domain = [("employee_id", "=", employeeObj.id)]
                    if date_begin and date_end:
                        domain += [('check_in', '>=', date_begin), ('check_in', '<=', date_end)]
                    attendacen_li = []
                    attendances = hrAttendance.with_company(context.get('company_id')).search(domain, limit=limit, offset=offset)
                    for empAtd in attendances:
                        _checkin = empAtd.check_in and mobikulFormatTimeZone(empAtd.check_in,employeeObj.tz) or ""
                        _checkout = empAtd.check_out and mobikulFormatTimeZone(empAtd.check_out,employeeObj.tz) or ""
                        attendacen_li.append({
                            "day":empAtd.check_in and empAtd.check_in.strftime('%A') or '',
                            "checkInDate":_checkin and _checkin.strftime('%Y-%m-%d') or '',
                            "checkOutDate":_checkout and _checkout.strftime('%Y-%m-%d') or '',
                            "checkinTime":_checkin and  _checkin.strftime('%I:%M %p') or '',
                            "checkoutTime":_checkout and _checkout.strftime('%I:%M %p') or '',
                        })
                    response["attendaceList"] = attendacen_li
        return self._response('Attendance History', response)

    @http.route('/v2/mobikul/odoo_attendance/passwordReset', type='http', auth="none", methods=['POST'],csrf = False)
    def passWordReset(self):
        response = self.__auth()
        if response.get('success'):
            mobikulAttendce = response.get('context').get("mobikulAttObj")
            if response.get('m_attendance_reset_password'):
                result = mobikulAttendce.resetPassword(self._mData.get('login', False))
            else:
                result = {
                    "success":False,
                    "message":_('Reset Password is not allowed'),
                    "responseCode":400
                }
            response.update(result)
        return self._response('resetPassword', response)

    @http.route('/v2/mobikul/odoo_attendance/allNotifications', type='http', auth="none", methods=['GET'],csrf = False)
    def getAllNotifications(self, **kwargs):
        response = self.__auth(authorize=True)
        if response.get('success'):
            Partner = response.get('context',{}).get('user').partner_id
            fields = ['id', 'name', 'title', 'subtitle', 'body', 'banner',
                      'icon', 'period', 'datatype', 'is_read', 'write_date']
            domain = [('customer_id', '=', Partner.id)]
            Message = request.env['mobikul.attendance.messages'].sudo()
            notification_message = Message.search_read(domain, limit=self._mData.get('limit', response.get(
                'itemsPerPage', 5)), offset=self._mData.get('offset', 0),  order="id desc", fields=fields)
            for msg in notification_message:
                msg['name'] = msg['name'] or ""
                msg['title'] = msg['title'] or ""
                msg['subtitle'] = msg['subtitle'] or ""
                msg['body'] = msg['body'] or ""
                msg['icon'] = _get_image_url(
                    self.base_url, 'mobikul.attendance.messages', msg['id'], 'icon', msg['write_date'])
                msg['banner'] = _get_image_url(
                    self.base_url, 'mobikul.attendance.messages', msg['id'], 'banner', msg['write_date'])
                msg.pop('write_date')
            result = {'all_notification_messages': notification_message}
            response.update(result)

        return self._response('notificationMessages', response)
