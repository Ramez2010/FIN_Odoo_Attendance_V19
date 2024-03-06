from odoo import _, api, fields, models
from datetime import datetime, timedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('struct_id')
    def fill_inputs_ids(self):
        inputs_ids = self.struct_id.input_line_type_ids
        self.input_line_ids = [(5, 0, 0)] + [(
            0,
            0,
            {
                'input_type_id': input.id
            },
        ) for input in inputs_ids]

    @api.model
    def default_get(self, fields_list):
        res = super(HrPayslip, self).default_get(fields_list)
        date_today = datetime.now().date()

        if date_today.day >= 26:
            date_from = datetime(date_today.year, date_today.month, 26)
            date_to = date_from + timedelta(days=30)
            date_to = date_to.replace(day=25)
        else:
            date_from = datetime(date_today.year, date_today.month - 1, 26)
            date_to = datetime(date_today.year, date_today.month, 25)

        res.update({
            'date_from': date_from,
            'date_to': date_to,
        })
        return res