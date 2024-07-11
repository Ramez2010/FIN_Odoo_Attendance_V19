# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class Overtime(models.Model):
    _name = 'overtime.request'
    _description = 'Overtime Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']


    ref = fields.Char(string='Reference', readonly=True, default='new')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today)
    project_id = fields.Many2one('account.analytic.account', string='Project', required=True)
    required_overtime_hours = fields.Float(string='Required Hours', required=True)
    description = fields.Html(string='Description', tracking=True)
    amount = fields.Float(string='Amount', default=0.0, compute='_compute_amount')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('ref', 'new') == 'new':
            vals['ref'] = self.env['ir.sequence'].next_by_code('overtime_seq') or 'new'
        res = super(Overtime, self).create(vals)
        return res

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})
            rec._create_journal_entry()

    def action_cancel(self):
        for rec in self:
            if rec.state == 'approved':
                rec._cancel_journal_entry()
                rec.write({'state': 'cancelled'})

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise exceptions.UserError('You can only delete records in draft state.')
        return super(Overtime, self).unlink()

    @api.depends('required_overtime_hours')
    def _compute_amount(self):
        for rec in self:
            if not rec.employee_id.contract_id:
                raise exceptions.ValidationError('Employee must have a contract.')
            if not rec.employee_id.contract_id.overtime_rate:
                raise exceptions.ValidationError('Employee contract must have an overtime rate.')
            rec.amount = rec.required_overtime_hours * rec.employee_id.contract_id.overtime_rate

    def _create_journal_entry(self):
        for rec in self:
            journal_id = int(self.env['ir.config_parameter'].sudo().get_param('overtime_journal_id'))
            debit_account_id = int(self.env['ir.config_parameter'].sudo().get_param('overtime_debit_account_id'))
            credit_account_id = int(self.env['ir.config_parameter'].sudo().get_param('overtime_credit_account_id'))
            jour_obj = self.env['account.journal'].search([('id', '=', journal_id)])
            currency_id = jour_obj.currency_id.id

            if not journal_id or not debit_account_id or not credit_account_id:
                raise exceptions.ValidationError('Overtime journal, debit account, and credit account must be set in general settings.')

            journal_entry = self.env['account.move'].create({
                'journal_id': jour_obj.id,
                'move_type': 'entry',
                'date': fields.Date.context_today(self),
                'ref': rec.ref,
                'currency_id': currency_id if currency_id else 1,
                'line_ids': [
                    (0, 0, {
                        'account_id': debit_account_id,
                        'name': rec.ref or 'Overtime Payment',
                        'debit': rec.amount,
                        'analytic_distribution': {rec.project_id.id: 100},
                    }),
                    (0, 0, {
                        'account_id': credit_account_id,
                        'name': rec.ref or 'Overtime Payment',
                        'credit': rec.amount,
                    }),
                ],
            })
            rec.journal_entry_id = journal_entry.id
            journal_entry.action_post()

    def _cancel_journal_entry(self):
        for rec in self:
            if rec.journal_entry_id:
                rec.journal_entry_id.button_draft()
                rec.journal_entry_id.button_cancel()
                # rec.journal_entry_id = False

    def _get_timesheet_hours(self, employee_id, date):
        timesheets = self.env['account.analytic.line'].search([
            ('employee_id', '=', employee_id),
            ('date', '=', date),
        ])
        total_hours = sum(timesheet.unit_amount for timesheet in timesheets)
        return total_hours

    @api.constrains('employee_id', 'request_date')
    def _check_timesheet_hours(self):
        for rec in self:
            if rec.request_date:
                timesheet_hours = self._get_timesheet_hours(rec.employee_id.id, rec.request_date)
                if timesheet_hours < rec.employee_id.resource_calendar_id.hours_per_day:
                    raise exceptions.ValidationError(
                        'Overtime request cannot be created or edited because the timesheet hours exceed 8 hours on the request date.')