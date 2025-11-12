from odoo import _, api, fields, models
from datetime import datetime, timedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        for rec in result:
            rec._compute_input_line_ids()
        return result

    def compute_sheet(self):
        for rec in self:
            rec._compute_input_line_ids()
        return super().compute_sheet()


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
            if date_today.month > 1:
                year = date_today.year
                month = date_today.month - 1
            else:
                year = date_today.year - 1
                month = 12

            day = 26
            date_from = datetime(year, month, day)
            # date_from = datetime(date_today.year, date_today.month - 1, 26)
            date_to = datetime(date_today.year, date_today.month, 25)

        res.update({
            'date_from': date_from,
            'date_to': date_to,
        })
        return res