
import logging
from odoo import api, fields, models, tools, SUPERUSER_ID, _, Command
from odoo.http import request
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import pytz
_logger = logging.getLogger(__name__)
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class AuthSignupHomeinherit(AuthSignupHome):
    def do_signup(self, qcontext):
        response = super(AuthSignupHomeinherit,self).do_signup(qcontext)
        if qcontext.get('token'):
            fcmObj = request.env['fcm.attendance.devices'].sudo()
            fcmObj.remove_all_devices(request.env.user.partner_id.id)
        return response

class UsersInheritAtd(models.Model):
    _inherit = 'res.users'

    @api.model
    def change_password(self, old_passwd, new_passwd):
        fcmObj = request.env['fcm.attendance.devices'].sudo()
        fcmObj.remove_all_devices(self.env.user.partner_id.id)
        return super(UsersInheritAtd,self).change_password(old_passwd, new_passwd)

    # @classmethod
    # def _login_custom(cls, db, credential, user_agent_env):
    #     login = credential['login']
    #     ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
    #     cr = cls.pool.cursor()
    #     self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
    #     try:
    #         with self._assert_can_auth(user=login):
    #             user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
    #             if not user:
    #                 raise AccessDenied()
    #             user = user.with_user(user)
    #             auth_info = user._check_credentials(credential, user_agent_env)
    #             tz = request.cookies.get('tz') if request else None
    #             if tz in pytz.all_timezones and (not user.tz or not user.login_date):
    #                 # first login or missing tz -> set tz to browser tz
    #                 user.tz = tz
    #             user._update_last_login()
    #             return user
    #     finally:
    #         # Ensure the cursor is not closed here, you can leave it open for other operations
    #         pass

    @classmethod
    def _login_custom(cls, login):
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        cr = cls.pool.cursor()
        self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
        try:
            with self._assert_can_auth(user=login):
                user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
                if not user:
                    raise AccessDenied()
                user = user.with_user(user)
                tz = request.cookies.get('tz') if request else None
                if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                    # first login or missing tz -> set tz to browser tz
                    user.tz = tz
                user._update_last_login()
                return user
        finally:
            # Ensure the cursor is not closed here, you can leave it open for other operations
            pass


class inheritChangePasswordUser(models.TransientModel):
    _inherit = 'change.password.user'

    def change_password_button(self):
        response = super(inheritChangePasswordUser,self).change_password_button()
        fcmObj = request.env['fcm.attendance.devices'].sudo()
        for line in self:
            fcmObj.remove_all_devices(line.user_id.partner_id.id)
        return response
