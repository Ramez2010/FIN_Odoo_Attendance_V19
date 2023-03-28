from odoo import _, api, fields, models


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
