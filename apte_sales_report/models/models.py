from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # TVQ_TVI_EX = fields.Float(store=True,
    #                           string='Total Quotation value (-) Total Invoiced Values Exclude taxes',
    #                           default=0.0, compute='_compute_TVQ_TVI_EX'
    #                           )
    # TVQ_TVI_INC = fields.Float(store=True,
    #                            string='Total Quotation value (-) Total Invoiced Values Include taxes',
    #                            default=0.0, compute='_compute_TVQ_TVI_INC'
    #                            )
    # IN_INC_QT_INC = fields.Float(store=True,
    #                              string='Total Invoices to Total Quotations (Include Taxes)%', default=0.0,
    #                              compute='_compute_IN_INC_QT_INC'
    #                              )
    # TVQ_DR = fields.Float(store=True,
    #                       string='Total Quotation value (-) Total Expenses for this analytic account Exclude taxes',
    #                       default=0.0, compute='_compute_TVQ_DR'
    #                       )
    # DR_TO_TVQ_EX = fields.Float(store=True,
    #                             string='Total Expense to Total Untaxed Amount (Quotations)%', default=0.0,
    #                             compute='_compute_TVQ_DR'
    #                             )
    # TVI_DR_EX = fields.Float(store=True,
    #                          string='Total Invoiced Values (-) Expenses for this analytic account Exclude taxes',
    #                          default=0.0, compute='_compute_TVI_DR_EX'
    #                          )
    # DR_TO_TVI_EX = fields.Float(store=True,
    #                             string='Total Expense to Total Untaxed Amount (Invoices)%', default=0.0,
    #                             compute='_compute_TVI_DR_EX'
    #                             )
    total_expense = fields.Float(store=True, precompute=True,
                                 default=0.0, compute='_compute_total_expense', string='Total Expense',
                                 )

    total_invoiced_untaxed = fields.Float(
        default=0.0,
        compute='_compute_total_invoiced_untaxed', string='Total Untaxed Invoiced',
    )

    total_invoiced = fields.Float(precompute=True,
                                  default=0.0, compute='_compute_total_invoiced', string='Total Invoiced'
                                  )

    pivot_total_payments = fields.Float(precompute=True,
                                        string='Total Payment Collected', default=0.0,
                                        compute='_compute_total_payments',
                                        )

    pivot_amount_due = fields.Float(compute='compute_amount_due', default=0.0, store=False, precompute=True,
                                    string='Total Payment Due')

    total_income = fields.Float(compute='_compute_total_income', default=0.0, store=True, precompute=True,
                                string='Total Income', )

    deduction = fields.Float(compute='_compute_total_deduction', default=0.0, precompute=True,
                             string='Total Deduction')

    quote_income = fields.Float(compute='_compute_quote_income', default=0.0, store=True, precompute=True,
                                string='Total Quotation Income')

    quote_income_percentage = fields.Float(compute='_compute_quote_income_percentage', default=0.0, store=True,
                                           precompute=True,
                                           string='Total Quotation Income %')

    quote_expense = fields.Float(compute='_compute_quote_expense', default=0.0, store=True, precompute=True,
                                 string='Total Quotation Expense')

    quote_expense_percentage = fields.Float(compute='_compute_quote_expense_percentage', default=0.0, store=True,
                                            precompute=True,
                                            string='Total Quotation Expense %')

    profit = fields.Float(compute='_compute_profit', default=0.0, store=True,
                          precompute=True,
                          string='Profit')
    profit_percentage = fields.Float(compute='_compute_profit_percentage', default=0.0, store=True,
                                     precompute=True,
                                     string='Profit %')

    income_expense = fields.Float(compute='_compute_income_expense', default=0.0, store=True, precompute=True,
                                  string='Income Expense')

    income_expense_percentage = fields.Float(compute='_compute_income_expense_percentage', default=0.0, store=True,
                                             precompute=True,
                                             string='Income Expense %')

    invoice_expense = fields.Float(compute='_compute_invoice_expense', default=0.0, store=True, precompute=True,
                                   string='Invoice Expense')

    invoice_expense_percentage = fields.Float(compute='_compute_invoice_expense_percentage', default=0.0, store=True,
                                              precompute=True,
                                              string='Invoice Expense %')
    egp_total = fields.Float(
        string='EGP Total',
        required=False, compute='_compute_egp_total')

    @api.depends('amount_total')
    def _compute_egp_total(self):
        for record in self:
            currency = record.currency_id
            converted_amount = currency.with_context(date=record.date_order).compute(record.amount_untaxed,
                                                                                   record.env.ref('base.EGP'))
            record.egp_total = converted_amount

    @api.depends('total_expense', 'total_invoiced_untaxed')
    def _compute_invoice_expense(self):
        for rec in self:
            rec.invoice_expense = rec.total_invoiced_untaxed - rec.total_expense

    @api.depends('total_expense', 'total_invoiced_untaxed')
    def _compute_invoice_expense_percentage(self):
        for rec in self:
            if rec.total_expense:
                rec.invoice_expense_percentage = rec.total_invoiced_untaxed / rec.total_expense - 1
            else:
                rec.invoice_expense_percentage = 0.0

    @api.depends('total_expense', 'total_income')
    def _compute_income_expense(self):
        for rec in self:
            rec.income_expense = rec.total_income - rec.total_expense

    @api.depends('total_expense', 'total_income')
    def _compute_income_expense_percentage(self):
        for rec in self:
            if rec.total_expense:
                rec.income_expense_percentage = rec.total_income / rec.total_expense - 1
            else:
                rec.income_expense_percentage = 0.0

    # @api.depends('analytic_account_id', 'analytic_account_id.credit')
    # def _compute_total_income(self):
    #     for rec in self:
    #         account_id = rec.analytic_account_id.id
    #         analytics = self.env['account.analytic.line'].search(
    #             [('amount', '>', 0), ('ref', 'not ilike', 'reversal'), ('account_id', '=', account_id)])
    #         credit = sum(analytic.amount for analytic in analytics)
    #         rec.total_income = credit

    @api.depends('analytic_account_id', 'analytic_account_id.credit')
    def _compute_total_income(self):
        for rec in self:
            account_id = rec.analytic_account_id.id
            analytics = self.env['account.analytic.line'].search([('account_id', '=', account_id), (
                'general_account_id.account_type', 'in', ['income', 'income_other'])])
            credit = sum(analytic.amount for analytic in analytics)
            rec.total_income = credit

    @api.depends('total_income', 'total_invoiced_untaxed')
    def _compute_total_deduction(self):
        for rec in self:
            rec.deduction = rec.total_income - rec.total_invoiced_untaxed

    # @api.depends('total_income', 'total_invoiced_untaxed')
    # def _compute_quote_income(self):
    #     for rec in self:
    #         rec.quote_income = rec.total_invoiced_untaxed - rec.total_income

    @api.depends('total_income', 'amount_untaxed')
    def _compute_quote_income(self):
        for rec in self:
            rec.quote_income = rec.amount_untaxed - rec.total_income

    # @api.depends('total_income', 'total_invoiced_untaxed')
    # def _compute_quote_income_percentage(self):
    #     for rec in self:
    #         if rec.total_invoiced_untaxed:
    #             rec.quote_income_percentage = (rec.total_income / rec.total_invoiced_untaxed) * 100
    #         else:
    #             rec.quote_income_percentage = 0.0

    @api.depends('total_income', 'amount_untaxed')
    def _compute_quote_income_percentage(self):
        for rec in self:
            if rec.amount_untaxed:
                rec.quote_income_percentage = (rec.total_income / rec.amount_untaxed) * 100
            else:
                rec.quote_income_percentage = 0.0

    # @api.depends('total_expense', 'total_invoiced_untaxed')
    # def _compute_quote_expense(self):
    #     for rec in self:
    #         rec.quote_expense = rec.total_invoiced_untaxed - rec.total_expense

    @api.depends('total_expense', 'amount_untaxed')
    def _compute_quote_expense(self):
        for rec in self:
            rec.quote_expense = rec.amount_untaxed - rec.total_expense

    # @api.depends('total_expense', 'total_invoiced_untaxed')
    # def _compute_quote_expense_percentage(self):
    #     for rec in self:
    #         if rec.total_invoiced_untaxed:
    #             rec.quote_expense_percentage = (rec.total_expense / rec.total_invoiced_untaxed)
    #         else:
    #             rec.quote_expense_percentage = 0.0

    @api.depends('total_expense', 'amount_untaxed')
    def _compute_quote_expense_percentage(self):
        for rec in self:
            if rec.amount_untaxed:
                rec.quote_expense_percentage = (rec.total_expense / rec.amount_untaxed)
            else:
                rec.quote_expense_percentage = 0.0

    @api.depends('total_expense', 'total_income')
    def _compute_profit(self):
        for rec in self:
            rec.profit = rec.total_income - rec.total_expense

    @api.depends('total_expense', 'total_income')
    def _compute_profit_percentage(self):
        for rec in self:
            if rec.total_expense:
                rec.profit_percentage = (rec.total_income / rec.total_expense)
            else:
                rec.profit_percentage = 0.0

    @api.depends('invoice_ids', 'invoice_ids.amount_residual_signed')
    def compute_amount_due(self):
        for rec in self:
            if rec.invoice_ids:
                rec.pivot_amount_due = sum(
                    invoice.amount_residual_signed for invoice in rec.invoice_ids if invoice.state == 'posted')
                # receipts = self.env['account.move'].search([
                #     ('partner_id', '=', rec.partner_id.id),
                #     ('move_type', '=', 'out_receipt'),
                #     ('sale_id', '=', rec.id),
                #     ('payment_state', '!=', 'reversed')
                # ])
                # if receipts:
                #     total_receipts = sum(receipts.mapped('amount_residual_signed'))
                #     rec.pivot_amount_due = total + total_receipts
                # else:
                #     rec.pivot_amount_due = total
            else:
                rec.pivot_amount_due = 0

    @api.depends('total_invoiced', 'pivot_amount_due')
    def _compute_total_payments(self):
        for rec in self:
            if rec.total_invoiced:
                rec.pivot_total_payments = rec.total_invoiced - rec.pivot_amount_due
            else:
                rec.pivot_total_payments = 0.0
            # if rec.invoice_ids:
            #     total = sum(invoice.total_paid_amount for invoice in rec.invoice_ids if invoice.state == 'posted')
            #     receipts = self.env['account.move'].search([
            #         ('partner_id', '=', rec.partner_id.id),
            #         ('move_type', '=', 'out_receipt'),
            #         ('sale_id', '=', rec.id),
            #         ('payment_state', '!=', 'reversed')
            #     ])
            #     if receipts:
            #         total_receipts = sum(invoice.total_paid_amount for invoice in receipts)
            #         rec.pivot_total_payments = total + total_receipts
            #     else:
            #         rec.pivot_total_payments = total
            # else:
            #     rec.pivot_total_payments = 0
            #

    @api.depends('invoice_ids', 'invoice_ids.amount_total_signed')
    def _compute_total_invoiced(self):
        for rec in self:
            if rec.invoice_ids:
                total_invoices = sum(
                    invoice.amount_total_signed for invoice in rec.invoice_ids if invoice.state == 'posted')

                receipts = self.env['account.move'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_type', '=', 'out_receipt'),
                    ('sale_id', '=', rec.id),
                    ('payment_state', '!=', 'reversed')
                ])
                if receipts:
                    total_receipts = sum(invoice.amount_total_signed for invoice in receipts)
                    rec.total_invoiced = total_invoices + total_receipts
                else:
                    rec.total_invoiced = total_invoices
            else:
                rec.total_invoiced = 0

    @api.depends('partner_id', 'invoice_ids', 'invoice_ids.amount_untaxed_signed', 'invoice_ids.state')
    def _compute_total_invoiced_untaxed(self):
        for rec in self:
            if rec.invoice_ids:
                total_invoices = sum(
                    invoice.amount_untaxed_signed for invoice in rec.invoice_ids if invoice.state == 'posted')

                receipts = self.env['account.move'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_type', '=', 'out_receipt'),
                    ('sale_id', '=', rec.id),
                    ('payment_state', '!=', 'reversed')
                ])
                if receipts:
                    total_receipts = sum(invoice.amount_untaxed_signed for invoice in receipts)
                    rec.total_invoiced_untaxed = total_invoices + total_receipts
                else:
                    rec.total_invoiced_untaxed = total_invoices
            else:
                rec.total_invoiced_untaxed = 0

    @api.depends('analytic_account_id', 'analytic_account_id.debit')
    def _compute_total_expense(self):
        for rec in self:
            account_id = rec.analytic_account_id.id
            analytics = self.env['account.analytic.line'].search([('account_id', '=', account_id), (
                'general_account_id.account_type', 'in', ['expense', 'expense_direct_cost', 'expense_depreciation'])])

            # analytics = self.env['account.analytic.line'].search(
            #     [('amount', '<', 0), ('ref', 'not ilike', 'reversal'), ('account_id', '=', account_id)])
            debit = sum(analytic.amount for analytic in analytics)
            rec.total_expense = debit * -1

    # @api.depends('amount_untaxed', 'total_invoiced_untaxed')
    # def _compute_TVQ_TVI_EX(self):
    #     for rec in self:
    #         rec.TVQ_TVI_EX = rec.amount_untaxed - rec.total_invoiced_untaxed
    #
    # @api.depends('amount_total', 'total_invoiced')
    # def _compute_TVQ_TVI_INC(self):
    #     for rec in self:
    #         rec.TVQ_TVI_INC = rec.amount_total - rec.total_invoiced
    #
    # @api.depends('total_invoiced', 'amount_total')
    # def _compute_IN_INC_QT_INC(self):
    #     for rec in self:
    #         rec.IN_INC_QT_INC = (rec.total_invoiced / rec.amount_total) if rec.amount_total != 0 else 0.0
    #
    # @api.depends('amount_untaxed', 'total_expense')
    # def _compute_TVQ_DR(self):
    #     for rec in self:
    #         rec.TVQ_DR = rec.amount_untaxed - rec.total_expense
    #         rec.DR_TO_TVQ_EX = (rec.total_expense / rec.amount_untaxed) if rec.amount_untaxed != 0 else 0.0
    #
    # @api.depends('total_invoiced_untaxed', 'total_expense')
    # def _compute_TVI_DR_EX(self):
    #     for rec in self:
    #         rec.TVI_DR_EX = rec.total_invoiced_untaxed - rec.total_expense
    #         if rec.total_expense == 0:
    #             rec.DR_TO_TVI_EX = 1
    #         else:
    #             rec.DR_TO_TVI_EX = (1 - (
    #                     rec.total_expense / rec.total_invoiced_untaxed)) if rec.total_invoiced_untaxed != 0 else 0.0


class InheritMove(models.Model):
    _inherit = 'account.move'

    total_paid_amount = fields.Float(compute='compute_total_paid_amount', store=False)

    @api.depends('invoice_payments_widget')
    def compute_total_paid_amount(self):
        for rec in self:
            if rec.invoice_payments_widget:
                amount_str = rec.invoice_payments_widget['content'][0]['amount_company_currency']
                clean_amount_str = ''.join(c for c in amount_str if c.isdigit() or c == '.')
                payment = float(clean_amount_str)
                rec.total_paid_amount = payment
            else:
                rec.total_paid_amount = 0.0

    # def compute_total_paid_amount(self):
    #     for rec in self:
    #         if rec.invoice_payments_widget:
    #             payment = float(rec.invoice_payments_widget['content'][0]['amount_company_currency'])
    #             rec.total_paid_amount = payment
    #         else:
    #             rec.total_paid_amount = 0.0
