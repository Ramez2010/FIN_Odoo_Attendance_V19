from odoo import _, api, fields, models, Command
from datetime import datetime, timedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        for rec in result:
            if hasattr(rec, '_compute_input_line_ids'):
                rec._compute_input_line_ids()
        return result

    def compute_sheet(self):
        for rec in self:
            if hasattr(rec, '_compute_input_line_ids'):
                rec._compute_input_line_ids()
        return super().compute_sheet()

    @api.onchange('struct_id')
    def fill_inputs_ids(self):
        if not self.struct_id:
            self.input_line_ids = [Command.clear()]
            return

        inputs_ids = self.struct_id.input_line_type_ids

        commands = [Command.clear()]
        for input_type in inputs_ids:
            commands.append(Command.create({
                'input_type_id': input_type.id
            }))

        self.input_line_ids = commands

    @api.model
    def default_get(self, fields_list):
        res = super(HrPayslip, self).default_get(fields_list)

        date_today = fields.Date.context_today(self)

        if date_today.day >= 26:
            date_from = datetime(date_today.year, date_today.month, 26).date()
            date_to_temp = datetime(date_today.year, date_today.month, 26) + timedelta(
                days=35)
            date_to = datetime(date_to_temp.year, date_to_temp.month, 25).date()
        else:
            if date_today.month > 1:
                year = date_today.year
                month = date_today.month - 1
            else:
                year = date_today.year - 1
                month = 12

            day = 26
            date_from = datetime(year, month, day).date()
            date_to = datetime(date_today.year, date_today.month, 25).date()

        res.update({
            'date_from': date_from,
            'date_to': date_to,
        })
        return res