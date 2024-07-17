from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    TVQ_TVI_EX = fields.Float(string='Total Quotation value (-) Total Invoiced Values Exclude taxes', default=0.0,
                              compute='_compute_TVQ_TVI_EX', )
    TVQ_TVI_INC = fields.Float(string='Total Quotation value (-) Total Invoiced Values include taxes', default=0.0,
                               compute='_compute_TVQ_TVI_INC')
    IN_INC_QT_INC = fields.Float(string='Total Invoices to Total Quotations (Include Taxes)%', default=0.0, compute='_compute_IN_INC_QT_INC')
    TVQ_DR = fields.Float(string='Total Quotation value (-) Total Expenses for this analytic account) Exclude taxes',
                          default=0.0, compute='_compute_TVQ_DR')
    DR_TO_TVQ_EX = fields.Float(string='Total Expense to Total untaxed amount (Quotations)%', default=0.0,
                                compute='_compute_TVQ_DR')
    TVI_DR_EX = fields.Float(string='Total Invoiced Values (-) Expenses for this analytic account) Exclude taxes',
                             default=0.0, compute='_compute_TVI_DR_EX')
    DR_TO_TVI_EX = fields.Float(string='Total Expense to Total untaxed amount (Invoices)%', default=0.0,
                                compute='_compute_TVI_DR_EX')

    @api.depends('order_line.price_subtotal', 'invoice_ids.amount_untaxed')
    def _compute_TVQ_TVI_EX(self):
        for rec in self:
            total_invoiced = sum(invoice.amount_untaxed for invoice in rec.invoice_ids)
            rec.TVQ_TVI_EX = rec.amount_untaxed - total_invoiced

    @api.depends('amount_total', 'invoice_ids.amount_total')
    def _compute_TVQ_TVI_INC(self):
        for rec in self:
            total_invoiced = sum(invoice.amount_total for invoice in rec.invoice_ids)
            rec.TVQ_TVI_INC = rec.amount_total - total_invoiced

    @api.depends('invoice_ids.amount_total', 'amount_total')
    def _compute_IN_INC_QT_INC(self):
        for rec in self:
            total_invoiced = sum(invoice.amount_total for invoice in rec.invoice_ids)
            if rec.amount_total != 0:
                rec.IN_INC_QT_INC = (total_invoiced / rec.amount_total) * 100
            else:
                rec.IN_INC_QT_INC = 0.0

    @api.depends('amount_untaxed', 'analytic_account_id')
    def _compute_TVQ_DR(self):
        for rec in self:
            if rec.analytic_account_id:
                total_expense = rec.analytic_account_id.debit
                rec.TVQ_DR = rec.amount_untaxed - total_expense
                rec.DR_TO_TVQ_EX = (total_expense / rec.amount_untaxed) * 100
            else:
                rec.TVQ_DR = 0.0
                rec.DR_TO_TVQ_EX = 0.0

    @api.depends('analytic_account_id', 'invoice_ids.amount_untaxed')
    def _compute_TVI_DR_EX(self):
        for rec in self:
            if rec.analytic_account_id:
                total_expense = rec.analytic_account_id.debit
                total_invoiced = sum(invoice.amount_untaxed for invoice in rec.invoice_ids)
                rec.TVI_DR_EX = total_invoiced - total_expense
                rec.DR_TO_TVI_EX = (total_expense / total_invoiced) * 100
            else:
                rec.TVI_DR_EX = 0.0
                rec.DR_TO_TVI_EX = 0.0
