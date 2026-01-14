from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        check_company=True,
    )

    total_expense = fields.Float(
        store=True,
        default=0.0,
        compute='_compute_total_expense',
        string='Total Expense',
        
    )

    total_invoiced_untaxed = fields.Float(
        store=True,
        default=0.0,
        compute='_compute_total_invoiced_untaxed',
        string='Total Untaxed Invoiced',
        
    )

    total_invoiced = fields.Float(
        store=True,
        default=0.0,
        compute='_compute_total_invoiced',
        string='Total Invoiced',
        
    )

    pivot_total_payments = fields.Float(
        store=True,
        string='Total Payment Collected',
        default=0.0,
        compute='_compute_total_payments',
        
    )

    pivot_amount_due = fields.Float(
        store=True,
        compute='compute_amount_due',
        default=0.0,
        string='Total Payment Due',
        
    )

    total_income = fields.Float(
        store=True,
        compute='_compute_total_income',
        default=0.0,
        string='Total Income',
        
    )

    deduction = fields.Float(
        store=True,
        compute='_compute_total_deduction',
        default=0.0,
        string='Total Deduction',
        
    )

    quote_income = fields.Float(
        store=True,
        compute='_compute_quote_income',
        default=0.0,
        string='Total Quotation Income',
        
    )

    quote_income_percentage = fields.Float(
        store=True,
        compute='_compute_quote_income_percentage',
        default=0.0,
        string='Total Quotation Income %',
        
    )

    quote_expense = fields.Float(
        store=True,
        compute='_compute_quote_expense',
        default=0.0,
        string='Total Quotation Expense',
        
    )

    quote_expense_percentage = fields.Float(
        store=True,
        compute='_compute_quote_expense_percentage',
        default=0.0,
        string='Total Quotation Expense %',
        
    )

    profit = fields.Float(
        store=True,
        compute='_compute_profit',
        default=0.0,
        string='Profit',
        
    )

    profit_percentage = fields.Float(
        store=True,
        compute='_compute_profit_percentage',
        default=0.0,
        string='Profit %',
        
    )

    income_expense = fields.Float(
        store=True,
        compute='_compute_income_expense',
        default=0.0,
        string='Income Expense',
        
    )

    income_expense_percentage = fields.Float(
        store=True,
        compute='_compute_income_expense_percentage',
        default=0.0,
        string='Income Expense %',
        
    )

    invoice_expense = fields.Float(
        store=True,
        compute='_compute_invoice_expense',
        default=0.0,
        string='Invoice Expense',
        
    )

    invoice_expense_percentage = fields.Float(
        store=True,
        compute='_compute_invoice_expense_percentage',
        default=0.0,
        string='Invoice Expense %',
        
    )

    egp_total = fields.Float(
        string='EGP Total',
        required=False,
        store=True,
        compute='_compute_egp_total',
        
    )


    @api.depends('amount_total', 'currency_id', 'date_order')
    def _compute_egp_total(self):
        egp_currency = self.env.ref('base.EGP', raise_if_not_found=False)
        for record in self:
            if egp_currency and record.currency_id:
                try:
                    record.egp_total = record.currency_id._convert(
                        record.amount_untaxed,
                        egp_currency,
                        record.company_id or self.env.company,
                        record.date_order or fields.Date.today()
                    )
                except Exception:
                    record.egp_total = 0.0
            else:
                record.egp_total = 0.0

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

    @api.depends('analytic_account_id')
    def _compute_total_income(self):
        orders_with_analytic = self.filtered('analytic_account_id')
        orders_without = self - orders_with_analytic
        orders_without.total_income = 0.0

        if not orders_with_analytic:
            return

        domain = [
            ('account_id', 'in', orders_with_analytic.analytic_account_id.ids),
            ('general_account_id.account_type', 'in', ['income', 'income_other'])
        ]
        groups = self.env['account.analytic.line'].read_group(
            domain, ['account_id', 'amount'], ['account_id']
        )
        amount_map = {g['account_id'][0]: g['amount'] for g in groups}

        for rec in orders_with_analytic:
            rec.total_income = amount_map.get(rec.analytic_account_id.id, 0.0)

    @api.depends('total_income', 'total_invoiced_untaxed')
    def _compute_total_deduction(self):
        for rec in self:
            rec.deduction = rec.total_income - rec.total_invoiced_untaxed

    @api.depends('total_income', 'amount_untaxed')
    def _compute_quote_income(self):
        for rec in self:
            rec.quote_income = rec.amount_untaxed - rec.total_income

    @api.depends('total_income', 'amount_untaxed')
    def _compute_quote_income_percentage(self):
        for rec in self:
            if rec.amount_untaxed:
                rec.quote_income_percentage = (rec.total_income / rec.amount_untaxed) * 100
            else:
                rec.quote_income_percentage = 0.0

    @api.depends('total_expense', 'amount_untaxed')
    def _compute_quote_expense(self):
        for rec in self:
            rec.quote_expense = rec.amount_untaxed - rec.total_expense

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

    @api.depends('invoice_ids', 'invoice_ids.amount_residual_signed', 'invoice_ids.state')
    def compute_amount_due(self):
        for rec in self:
            total = 0.0
            if rec.invoice_ids:
                posted = rec.invoice_ids.filtered(lambda i: i.state == 'posted')
                total = sum(posted.mapped('amount_residual_signed'))
            rec.pivot_amount_due = total

    @api.depends('total_invoiced', 'pivot_amount_due')
    def _compute_total_payments(self):
        for rec in self:
            rec.pivot_total_payments = rec.total_invoiced - rec.pivot_amount_due

    @api.depends('invoice_ids', 'invoice_ids.amount_total_signed', 'invoice_ids.state')
    def _compute_total_invoiced(self):
        for rec in self:
            total = 0.0
            if rec.invoice_ids:
                posted = rec.invoice_ids.filtered(lambda i: i.state == 'posted')
                total = sum(posted.mapped('amount_total_signed'))

                # البحث عن الإيصالات
                receipts = self.env['account.move'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_type', '=', 'out_receipt'),
                    ('payment_state', '!=', 'reversed')
                ])
                if receipts:
                    total += sum(receipts.mapped('amount_total_signed'))
            rec.total_invoiced = total

    @api.depends('invoice_ids', 'invoice_ids.amount_untaxed_signed', 'invoice_ids.state')
    def _compute_total_invoiced_untaxed(self):
        for rec in self:
            total = 0.0
            if rec.invoice_ids:
                posted = rec.invoice_ids.filtered(lambda i: i.state == 'posted')
                total = sum(posted.mapped('amount_untaxed_signed'))

                receipts = self.env['account.move'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_type', '=', 'out_receipt'),
                    ('payment_state', '!=', 'reversed')
                ])
                if receipts:
                    total += sum(receipts.mapped('amount_untaxed_signed'))
            rec.total_invoiced_untaxed = total

    @api.depends('analytic_account_id')
    def _compute_total_expense(self):
        orders_with_analytic = self.filtered('analytic_account_id')
        orders_without = self - orders_with_analytic
        orders_without.total_expense = 0.0

        if not orders_with_analytic:
            return

        domain = [
            ('account_id', 'in', orders_with_analytic.analytic_account_id.ids),
            ('general_account_id.account_type', 'in', ['expense', 'expense_direct_cost', 'expense_depreciation'])
        ]

        groups = self.env['account.analytic.line'].read_group(
            domain, ['account_id', 'amount'], ['account_id']
        )
        amount_map = {g['account_id'][0]: g['amount'] for g in groups}

        for rec in orders_with_analytic:
            rec.total_expense = amount_map.get(rec.analytic_account_id.id, 0.0) * -1


class InheritMove(models.Model):
    _inherit = 'account.move'

    total_paid_amount = fields.Float(
        compute='compute_total_paid_amount',
        store=False
    )

    @api.depends('invoice_payments_widget')
    def compute_total_paid_amount(self):
        for rec in self:
            rec.total_paid_amount = 0.0
            if rec.invoice_payments_widget:
                try:
                    widget_content = rec.invoice_payments_widget.get('content', [])
                    if widget_content and isinstance(widget_content, list):
                        amount_str = widget_content[0].get('amount_company_currency', '0')
                        clean_amount_str = ''.join(c for c in amount_str if c.isdigit() or c == '.')
                        rec.total_paid_amount = float(clean_amount_str) if clean_amount_str else 0.0
                except Exception:
                    pass