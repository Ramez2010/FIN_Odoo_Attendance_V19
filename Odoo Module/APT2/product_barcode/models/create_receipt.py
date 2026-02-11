from odoo import models, fields, api, SUPERUSER_ID, Command
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    receipt_quantity = fields.Float(string="Receipt Quantity", digits='Product Unit of Measure')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    selection_invoice = fields.Selection([('invoice', 'Invoice'), ('receipt', 'Receipt')], required=True,
                                         default='invoice')

    flag = fields.Boolean('Flag')

    receipt_count = fields.Integer(compute='compute_receipts_count')

    @api.onchange('selection_invoice')
    def _onchange_selection_invoice(self):
        if self.selection_invoice == 'receipt':
            self.get_receipt_quantity()

    def get_receipt_quantity(self):
        for rec in self:
            rec.order_line.receipt_quantity = 0.0


            receipts = self.env['account.move'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('move_type', '=', 'out_receipt'),
                ('sale_id', '=', rec.id)
            ])

            product_quantities = {}
            for receipt in receipts:

                for line in receipt.invoice_line_ids:
                    if line.product_id:
                        qty = line.quantity
                        product_quantities[line.product_id.id] = product_quantities.get(line.product_id.id, 0) + qty

            for line in rec.order_line:
                if line.product_id.id in product_quantities:
                    line.receipt_quantity = product_quantities[line.product_id.id]

    def create_receipt(self):
        self.ensure_one()
        self.flag = True


        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise ValidationError("No Sales Journal found!")

        lines = []
        for line in self.order_line:
            qty_to_receipt = line.product_uom_qty - line.receipt_quantity
            if qty_to_receipt > 0:
                account = line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id
                if not account:
                    raise ValidationError(f"Please define Income Account for product: {line.product_id.name}")

                lines.append(Command.create({
                    'product_id': line.product_id.id,
                    'price_unit': line.price_unit,
                    'account_id': account.id,
                    'name': line.name,
                    'quantity': qty_to_receipt,
                    'tax_ids': [Command.set(line.tax_id.ids)],
                    'currency_id': self.currency_id.id,
                }))

        if not lines:
            return

        receipt_vals = {
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'move_type': 'out_receipt',
            'sale_id': self.id,
            'journal_id': journal.id,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': lines,
        }

        if hasattr(self, 'analytic_account_id') and self.analytic_account_id:
            receipt_vals['analytic_account_id_2'] = self.analytic_account_id.id
        # ----------------------------------------------

        receipt = self.env['account.move'].with_user(SUPERUSER_ID).create(receipt_vals)
        return receipt

    @api.depends('partner_id')
    def compute_receipts_count(self):
        for rec in self:
            rec.receipt_count = self.env['account.move'].search_count([
                ('partner_id', '=', rec.partner_id.id),
                ('move_type', '=', 'out_receipt'),
                ('sale_id', '=', rec.id)
            ])
            rec.get_receipt_quantity()

    def get_receipt(self):
        self.ensure_one()

        ctx = {
            'default_move_type': 'out_receipt',
            'default_sale_id': self.id,
            'default_partner_id': self.partner_id.id,
        }

        if hasattr(self, 'analytic_account_id') and self.analytic_account_id:
            ctx['default_analytic_account_id_2'] = self.analytic_account_id.id
        # --------------------------------------------------

        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipts',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('sale_id', '=', self.id), ('move_type', '=', 'out_receipt')],
            'context': ctx,
        }


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order', string='Sale Order', readonly=True, copy=False)

    analytic_account_id_2 = fields.Many2one('account.analytic.account', string='Analytic Account (Receipts)')