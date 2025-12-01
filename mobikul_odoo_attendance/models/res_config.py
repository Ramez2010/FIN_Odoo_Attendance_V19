# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)


class MobileAttendanceSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _default_m_attendance(self):
        return self.env['mobikul.attendance'].search([], limit=1).id

    mobikul_atd_app = fields.Many2one('mobikul.attendance', string="Mobikul Attendance APP",
                                  default=_default_m_attendance)
    attendance_app_name = fields.Char('App Name', related='mobikul_atd_app.name')
    m_attendance_reset_password = fields.Boolean(
        string='Enable password reset', help="This allows users to trigger a password reset from App")

    @api.model
    def get_values(self):
        res = super(MobileAttendanceSettings, self).get_values()
        IrConfigParam = self.env['ir.config_parameter']
        res.update(
            m_attendance_reset_password=safe_eval(IrConfigParam.get_param(
                'auth_signup.reset_password', 'False')),
        )
        return res

    def set_values(self):
        self.ensure_one()
        super(MobileAttendanceSettings, self).set_values()
        IrConfigParam = self.env['ir.config_parameter']
        IrConfigParam.set_param('auth_signup.reset_password', repr(self.m_attendance_reset_password))

    def open_mobikul_attendance_conf(self):
        _logger.info("this is self id we need %r",self.mobikul_atd_app.id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mobikul-Attendance-App Configuration',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mobikul.attendance',
            'res_id':self.mobikul_atd_app.id,
            'target': 'current',
        }
