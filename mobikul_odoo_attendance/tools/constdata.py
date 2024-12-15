from ast import literal_eval
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime
from odoo.exceptions import UserError
import json
import logging
import requests
from datetime import datetime
from odoo.http import request
from pytz import timezone
import pytz
_logger = logging.getLogger(__name__)
import re

def fcmDeviceCheck(self,user,dontCheck=False):
    '''
        This function is used to manage reset case and logout from all device case
        In case of reset passwrd customer id will removed from registered device
        So all device get Unregistered and we dont allow any API to hit without device id
    '''
    response = {"success":True}
    fcmObj = request.env['fcm.attendance.devices'].sudo()
    if fcmObj.search_count([("customer_id","=",user.partner_id.id)]) == 0 and not dontCheck:
        response.update({
            "success":False,
            "loginAgain":True,
            "message":_('Authorization Revoked Please Login Again!'),
            "responseCode":400
        })
    return response

def fcmDeviceCheckAlreadyAssignedToUser(self,userId,deviceId):
    '''
        This function is used to check if the customer has assigned_id already or the deviceId
        is already used. We want to restrict that multiple users use the same device.
    '''
    response = {"success":True}
    fcmObj = request.env['fcm.attendance.devices'].sudo()
    if fcmObj.search_count([("customer_id","=",userId)]) == 0 and fcmObj.search_count([("device_id","=",deviceId)]) == 0:
        return response

    if fcmObj.search_count([("customer_id","=",userId), ("device_id","=",deviceId)]) == 1:
        return response

    response.update({
        "success":False,
        "loginAgain":True,
        "message":_('The user is logged in before using another phone or this phone was used by another user. Contact your HR for support!'),
        "responseCode":400
    })
    return response

def _pushNotification(token, condition='signup', customer_id=False):
    notifications = request.env['mobikul.attendance.notification.template'].sudo().search([
        ('condition', '=', condition)])
    for n in notifications:
        n._send({'to': token}, customer_id)
    return True

def _languageData(context):
    mobileAttndOb = context.get("mobikulAttObj")
    temp = {
        'defaultLanguage': (mobileAttndOb.default_lang.code, mobileAttndOb.default_lang.name),
        'allLanguages': [(id.code, id.name) for id in mobileAttndOb.language_ids],
    }
    return temp

def mobikul_display_address(address, name=""):
    return (name or "") + (name and "\n" or "") + address

def mobikulFormatTimeZone(date,tz = False):
    """To convert the time to specific timezone"""
    tz_name = tz or 'UTC'
    try:
        localized_datetime = date.astimezone(timezone(tz_name))
    except Exception as e:
        localized_datetime = date
    return localized_datetime

def check_addons(self):
    """TO check the addons and provide it in splash page api"""
    result = {}
    ir_model_obj = request.env['ir.module.module'].sudo()
    result['hr_attendance'] = ir_model_obj.search(
        [('state', '=', 'installed'), ('name', '=', 'hr_attendance')]) and True or False
    return result

def getDefaultData(self,mobAtdObj):
    """TO check the default setting ape provide it in splash page api"""
    IrConfigParam = request.env['ir.config_parameter'].sudo()
    temp = {}
    temp['m_attendance_reset_password'] = literal_eval(
            IrConfigParam.get_param('auth_signup.reset_password', 'False'))
    temp['allow_signup'] = False
    temp['privacy_policy_url'] = mobAtdObj.privacy_policy
    temp["addons"] = check_addons(self)
    return temp

def _get_image_url(base_url, model_name, record_id, field_name, write_date=0, width=0, height=0):
    """ Returns a local url that points to the image field of a given browse record. """
    if base_url and not base_url.endswith("/"):
        base_url = base_url+"/"
    if width or height:
        return '%sweb/image/%s/%s/%s/%sx%s?unique=%s' % (base_url, model_name, record_id, field_name, width, height, re.sub('[^\d]', '', fields.Datetime.to_string(write_date)))
    else:
        return '%sweb/image/%s/%s/%s?unique=%s' % (base_url, model_name, record_id, field_name, re.sub('[^\d]', '', fields.Datetime.to_string(write_date)))

def _get_employee_profile_url(base_url, record_id, write_date=0):
    """ Returns a local url that points to the image field of a given browse record. """
    if base_url and not base_url.endswith("/"):
        base_url = base_url+"/"
    return '%simage/employee/%s?unique=%s' % (base_url, record_id, re.sub('[^\d]', '', fields.Datetime.to_string(write_date)))

def _tokenUpdate(self, customer_id=False,removeAllAuth=False):
    FcmRegister = request.env['fcm.attendance.devices'].sudo()
    already_registered = FcmRegister.search(
        [('device_id', '=', self._mData.get("fcmDeviceId"))])
    if already_registered:
        already_registered.write(
            {'token': self._mData.get("fcmToken"), 'customer_id': customer_id})
    else:
        FcmRegister.create({
            'token': self._mData.get("fcmToken", ""),
            'device_id': self._mData.get("fcmDeviceId", ""),
            'description': "%r" % self._mData,
            'customer_id': customer_id,
        })
    return True
def _easy_date(time=False):
    """
    Get a datetime object or a timestamp and return a
    easy read string like 'Just now', 'Yesterday', '3 months ago',
    'Year ago'.
    """
    now = datetime.now()
    if type(time) is str:
        time = fields.Datetime.from_string(time)
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(int(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(int(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(int(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(int(day_diff / 30)) + " months ago"
    return str(int(day_diff / 365)) + " years ago"
