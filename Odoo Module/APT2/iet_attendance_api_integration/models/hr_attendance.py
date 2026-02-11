from odoo import fields, models, api, _


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    message_out = fields.Char('Check out message')
    analytic_account_id = fields.Many2one("account.analytic.account", string="Account Analytic")

    @api.model
    def _cron_attendance_auto_check_out(self):
        # action_date = fields.Datetime.now()
        attendance_ids = self.env['hr.attendance'].sudo().search(
            [('check_in', '!=', False)])
        for attendance in attendance_ids:
            if attendance.check_in.date() == fields.Date.today():
                check_in = attendance.check_in
                close_check_out = check_in.replace(hour=20, minute=58)
                attendance.sudo().check_out = close_check_out
                attendance.sudo().message_out = "Auto Close Check Out"