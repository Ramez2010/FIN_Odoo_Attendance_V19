from ast import literal_eval
from odoo import api, fields, models, _, SUPERUSER_ID
from datetime import datetime
from odoo.exceptions import UserError
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
        lc = self.env['ir.default']._get('res.partner', 'lang')
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

    name = fields.Char('Mobile Attendance App Title', default="Mobikul Attendance App", required=True)
    api_key = fields.Char(string='API Secret key', default="dummySecretKey", required=True)
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
