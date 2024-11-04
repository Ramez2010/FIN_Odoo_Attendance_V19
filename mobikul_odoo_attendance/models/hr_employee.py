from odoo import api, fields, models, exceptions, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _attendance_action_change_from_api(self, geolocation_tracking=False, latitude=False, longitude=False):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = fields.Datetime.now()

        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
                'geolocation_tracking': geolocation_tracking,
                'check_in_latitude': latitude,
                'check_in_longitude': longitude,
            }
            return self.env['hr.attendance'].create(vals)
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)],
                                                      limit=1)
        if attendance:
            attendance.check_out = action_date
            attendance.check_out_latitude = latitude
            attendance.check_out_longitude = longitude
        else:
            raise exceptions.UserError(
                _('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                  'Your attendances have probably been modified manually by human resources.') % {
                    'empl_name': self.sudo().name, })
        return attendance
