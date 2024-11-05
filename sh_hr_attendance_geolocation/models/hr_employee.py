# Part of Softhealer Technologies.
from odoo import models, fields,  exceptions, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    #inherited hr.employee model to override methods
    def sh_attendance_manual(self, vals, next_action, entered_pin=None):
        self.ensure_one()
        can_check_without_pin = not self.env.user.has_group('hr_attendance.group_hr_attendance_use_pin') or (
            self.user_id == self.env.user and entered_pin is None)
        if can_check_without_pin or entered_pin is not None and entered_pin == self.sudo().pin:
            return self.sh_attendance_action(next_action, vals)
        return {'warning': _('Wrong PIN')}

    def sh_attendance_action(self, next_action, vals):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()
        employee = self.sudo()
        message = vals
        action_message = self.env.ref(
            'hr_attendance.hr_attendance_action_greeting_message').read()[0]
        action_message['previous_attendance_change_date'] = employee.last_attendance_id and (
            employee.last_attendance_id.check_out or employee.last_attendance_id.check_in) or False
        action_message['employee_name'] = employee.name
        action_message['barcode'] = employee.barcode
        action_message['next_action'] = next_action
        action_message['hours_today'] = employee.hours_today

        if employee.user_id:
            modified_attendance = employee.with_user(
                employee.user_id).sh_attendance_action_change(message)
        else:
            modified_attendance = employee.sh_attendance_action_change(message)
        action_message['attendance'] = modified_attendance.read()[0]
        return {'action': action_message}

    def sh_attendance_action_change(self, message):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        check_in_out_message = message[0]
        vals = {}
        latitude = message[1]
        longitude = message[2]
        analytic_account_id = message[3]
        url = "http://maps.google.com/maps?"

        url = "http://maps.google.com/maps?q=" + \
            str(latitude) + ',' + str(longitude)

        if url:
            vals = {'check_in_url': url}

        if len(self) > 1:
            raise exceptions.UserError(
                _('Cannot perform check in or check out on multiple employees.'))
        action_date = fields.Datetime.now()

        if self.attendance_state != 'checked_in':
            vals.update({
                'employee_id': self.id,
                'check_in': action_date,
                'message_in': check_in_out_message,
            })
            if latitude and longitude:
                vals.update({
                    'in_latitude': latitude,
                    'in_longitude': longitude,
                })
            if analytic_account_id:
                vals.update({"analytic_account_id": analytic_account_id})
            return self.env['hr.attendance'].create(vals)

        else:
            attendance = self.env['hr.attendance'].search(
                [('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
            attendance.message_out = check_in_out_message
            if latitude and longitude:
                attendance.check_out_url = url
                attendance.out_latitude = latitude
                attendance.out_longitude = longitude
            if analytic_account_id:
                attendance.analytic_account_id = analytic_account_id
            if attendance:
                attendance.check_out = action_date
            else:
                raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                                             'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.name, })
            return attendance
