from odoo import models, fields, api
import calendar
from datetime import date
import re



class ContractInherit(models.Model):
    _inherit = 'hr.contract'

    hourly_rate_ids = fields.One2many('employee.hourly.rate', 'contract_id', string='Hourly Rates', compute='_onchange_date')

    current_year = fields.Integer(compute='_get_current_year')

    def _get_current_year(self):
        for rec in self:
            if date.today().year != rec.current_year:
                rec.current_year = date.today().year

    @api.onchange('date_start', 'date_end', 'current_year')
    def _onchange_date(self):
        for contract in self:
            contract_id = self.extract_integer(str(contract.id))
            print(contract_id)
            print(contract.employee_id.id)
            start_date = contract.date_start
            if contract.date_end:
                end_date = contract.date_end
            else:
                end_date = date(contract.current_year, 12, 31)
            # Remove Extra Lines
            hourly_rates_to_delete1 = self.env['employee.hourly.rate'].sudo().search([
                ('contract_id', '=', contract_id),('date', '>', end_date)
            ])
            hourly_rates_to_delete2 = self.env['employee.hourly.rate'].sudo().search([
                ('employee_id', '=', contract.employee_id.id), ('contract_id.date_start', '<', contract.date_start),
                 ('date', '>=', date(start_date.year, start_date.month, 1))
            ])
            if hourly_rates_to_delete1:
                hourly_rates_to_delete1.sudo().unlink()
            if hourly_rates_to_delete2:
                hourly_rates_to_delete2.sudo().unlink()
            current_date = date(start_date.year, start_date.month, 1)
            while current_date <= end_date:
                hourly_rate_id1 = self.env['employee.hourly.rate'].sudo().search([
                    ('contract_id', '=', contract_id),
                    ('date', '=', current_date)
                ])
                hourly_rate_id2 = self.env['employee.hourly.rate'].sudo().search([
                    ('employee_id', '=', contract.employee_id.id), ('contract_id.date_start', '>', contract.date_start),
                    ('date', '=', current_date)
                ])

                if not hourly_rate_id1 and not hourly_rate_id2:
                    new_hourly_rate_id = self.env['employee.hourly.rate'].sudo().create({
                        'contract_id': contract_id,
                        'date': current_date,
                    })
                # Move to the next month
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, 1)
                else:
                    current_date = date(current_date.year, current_date.month + 1, 1)

    def _hourly_rate_ids(self):
        contracts = self.search([], order="date_start asc")
        for contract in contracts:
            contract_id = self.extract_integer(str(contract.id))
            start_date = contract.date_start
            if contract.date_end:
                end_date = contract.date_end
            else:
                end_date = date(contract.current_year, 12, 31)
            # Remove Extra Lines
            hourly_rates_to_delete1 = self.env['employee.hourly.rate'].sudo().search([
                ('contract_id', '=', contract_id), ('date', '>', end_date)
            ])
            hourly_rates_to_delete2 = self.env['employee.hourly.rate'].sudo().search([
                ('employee_id', '=', contract.employee_id.id), ('contract_id.date_start', '<', contract.date_start),
                ('date', '>=', date(start_date.year, start_date.month, 1))
            ])
            if hourly_rates_to_delete1:
                hourly_rates_to_delete1.sudo().unlink()
            if hourly_rates_to_delete2:
                hourly_rates_to_delete2.sudo().unlink()
            current_date = date(start_date.year, start_date.month, 1)
            while current_date <= end_date:
                hourly_rate_id1 = self.env['employee.hourly.rate'].sudo().search([
                    ('contract_id', '=', contract_id),
                    ('date', '=', current_date)
                ])
                print("1")
                print(hourly_rate_id1)
                hourly_rate_id2 = self.env['employee.hourly.rate'].sudo().search([
                    ('employee_id', '=', contract.employee_id.id), ('contract_id.date_start', '>', contract.date_start),
                    ('date', '=', current_date)
                ])
                print("2")
                print(hourly_rate_id2)
                if not hourly_rate_id1 and not hourly_rate_id2:
                    new_hourly_rate_id = self.env['employee.hourly.rate'].sudo().create({
                        'contract_id': contract_id,
                        'date': current_date,
                    })
                # Move to the next month
                if current_date.month == 12:
                    current_date = date(current_date.year + 1, 1, 1)
                else:
                    current_date = date(current_date.year, current_date.month + 1, 1)



    def extract_integer(self, s):
        match = re.search(r'\d+', s)
        return int(match.group()) if match else None
