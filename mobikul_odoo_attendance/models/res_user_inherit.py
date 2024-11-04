
import logging
from odoo import _, api, fields, models
from odoo.http import request
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

class inheritChangePasswordUser(models.TransientModel):
    _inherit = 'change.password.user'

    def change_password_button(self):
        response = super(inheritChangePasswordUser,self).change_password_button()
        fcmObj = request.env['fcm.attendance.devices'].sudo()
        for line in self:
            fcmObj.remove_all_devices(line.user_id.partner_id.id)
        return response
