from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    receipt_quantity = fields.Float()


class SubCategory(models.Model):
    _inherit = 'sale.order'

    selection_invoice = fields.Selection([('invoice', 'Invoice'), ('receipt', 'Receipt')], required=True,default='invoice')

    @api.constrains()
    def change(self):
        print("suceesss")
        self.get_receipt_quantity()

    def get_receipt_quantity(self):
        for rec in self:
            # Initialize the receipt quantity
            rec.order_line.receipt_quantity = 0.0

            # Search for related receipts
            receipts = self.env['account.move'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('move_type', '=', 'out_receipt'),
                ('sale_id', '=', rec.id)
            ])
            print(receipts, "rrreccee")

            for receipt in receipts:
                # Sum up the quantities from the matched sale order lines
                for line in receipt.line_ids:
                    # if line.sale_line_ids and line.sale_line_ids.id == rec.id:
                    rec.order_line.receipt_quantity += line.quantity

    flag = fields.Boolean('Flag')

    def create_receipt(self):
        self.flag = True
        journal = 16
        receipt_vals = {
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'move_type': 'out_receipt',
            'analytic_account_id_2': self.analytic_account_id.id,
            'sale_id': self.id,
            'journal_id': journal,
            'invoice_line_ids':
                self.order_line.mapped(lambda line: (0, 0,
                                                     {'product_id': line.product_id.id,
                                                      'price_unit': line.price_unit,
                                                      'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
                                                      'name': line.name,
                                                      'quantity': line.product_uom_qty - line.receipt_quantity,
                                                      'tax_ids': line.tax_id}))}
        receipt = self.env['account.move'].with_user(SUPERUSER_ID).create(receipt_vals)

        # self.get_receipt_quantity()
        return receipt

    receipt_count = fields.Integer(
        compute='compute_receipts_count')

    @api.depends('partner_id')
    def compute_receipts_count(self):
        for rec in self:
            receipts = self.env['account.move'].search_count([
                ('partner_id', '=', rec.partner_id.id), ('move_type', '=', 'out_receipt'), ('sale_id', '=', self.id)
            ])
            rec.receipt_count = receipts
            self.get_receipt_quantity()

    def get_receipt(self):
        account_move = self.env['account.move'].search(
            [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)])
        currency_id = account_move.currency_id.id if account_move else self.env.ref('base.main_company').currency_id.id

        self.ensure_one()
        default_partner_id = self.partner_id.id
        # original_quantity = self.order_line.product_uom_qty
        # print(original_quantity, '------------------------------------------------------')
        default_order_lines = self.order_line.mapped(lambda line: (0, 0,
                                                                   {'product_id': line.product_id.id,
                                                                    'price_unit': line.price_unit,
                                                                    'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
                                                                    'name': line.name,
                                                                    'quantity': line.product_uom_qty,
                                                                    'currency_id': currency_id,
                                                                    }))
        receipt_journal = 16
        analytic = self.analytic_account_id.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipts',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)],
            'context': {'default_move_type': 'out_receipt',
                        'default_partner_id': default_partner_id,
                        'default_sale_id': self.id,
                        'default_analytic_account_id_2': analytic,
                        'default_journal_id': receipt_journal,
                        'default_invoice_line_ids': default_order_lines
                        },
        }

    # def get_receipt(self):
    #     account_move = self.env['account.move'].search(
    #         [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)], limit=1)
    #
    #     self.ensure_one()
    #     default_partner_id = self.partner_id.id
    #
    #     # Get currency from account move or set a default
    #     currency_id = account_move.currency_id.id if account_move else self.env.ref('base.main_company').currency_id.id
    #
    #     default_order_lines = self.order_line.mapped(lambda line: (0, 0,
    #                                                                {'product_id': line.product_id.id,
    #                                                                 'price_unit': line.price_unit,
    #                                                                 'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
    #                                                                 'name': line.name,
    #                                                                 'quantity': line.product_uom_qty,
    #                                                                 'currency_id': currency_id
    #                                                                 }))
    #
    #     receipt_journal = 16
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Receipts',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.move',
    #         'domain': [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)],
    #         'context': {'default_move_type': 'out_receipt',
    #                     'default_partner_id': default_partner_id,
    #                     'default_currency_id': currency_id,
    #                     'default_sale_id': self.id,
    #                     'default_journal_id': receipt_journal,
    #                     'default_invoice_line_ids': default_order_lines},
    #     }

    # def get_receipt(self):
    #     account_move = self.env['account.move'].search(
    #         [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)], limit=1)
    #
    #     self.ensure_one()
    #     default_partner_id = self.partner_id.id
    #
    #     # Get currency from account move or set a default
    #     currency_id = account_move.currency_id.id if account_move else self.env.ref('base.main_company').currency_id.id
    #
    #     default_order_lines = [(5, 0, 0)]  # Command to delete all existing records
    #     default_order_lines += self.order_line.mapped(lambda line: (0, 0,
    #                                                                 {'product_id': line.product_id.id,
    #                                                                  'price_unit': line.price_unit,
    #                                                                  'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
    #                                                                  'name': line.name,
    #                                                                  'quantity': line.product_uom_qty,
    #                                                                  'currency_id': currency_id
    #                                                                  }))
    #
    #     receipt_journal = 16
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Receipts',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.move',
    #         'domain': [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)],
    #         'context': {'default_move_type': 'out_receipt',
    #                     'default_partner_id': default_partner_id,
    #                     'default_currency_id': currency_id,
    #                     'default_sale_id': self.id,
    #                     'default_journal_id': receipt_journal,
    #                     'default_invoice_line_ids': default_order_lines},
    #     }

    # def get_receipt(self):
    #     self.ensure_one()
    #
    #     # Search for an existing account move or prepare to create a new one
    #     account_move = self.env['account.move'].search(
    #         [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)], limit=1)
    #
    #     # Determine the currency
    #     currency_id = account_move.currency_id.id if account_move else self.env.ref('base.main_company').currency_id.id
    #     # analytic = self.analytic_account_id.id
    #     # Prepare the invoice lines
    #
    #     invoice_lines = [(0, 0, {
    #         'product_id': line.product_id.id,
    #         'price_unit': line.price_unit,
    #         'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
    #         'name': line.name,
    #         'quantity': line.product_uom_qty,
    #         'currency_id': currency_id
    #     }) for line in self.order_line]
    #
    #     # Create a new account move if one does not exist
    #     if not account_move:
    #         account_move = self.env['account.move'].create({
    #             'move_type': 'out_receipt',
    #             'partner_id': self.partner_id.id,
    #             'currency_id': currency_id,
    #             'sale_id': self.id,
    #             'journal_id': 16,
    #             'analytic_account_id_2': self.analytic_account_id.id,
    #             'line_ids': invoice_lines,
    #         })
    #
    #     # Return an action to open the form view of the created/found account move
    #     # return {
    #     #     'type': 'ir.actions.act_window',
    #     #     'name': 'Receipts',
    #     #     'view_mode': 'form',
    #     #     'res_model': 'account.move',
    #     #     'res_id': account_move.id,
    #     #     'context': {'form_view_initial_mode': 'edit'},  # Open in edit mode if needed
    #     # }
    #
    #     # return {
    #     #     'type': 'ir.actions.act_window',
    #     #     'name': 'Receipts',
    #     #     'view_mode': 'tree,form',  # Start with the tree view, but also allow opening records in form view
    #     #     'res_model': 'account.move',
    #     #     'domain': [('sale_id', '=', self.id)],  # Optional: Filter records related to the current sale order
    #     #     'context': {
    #     #         'default_sale_id': self.id,  # Set default values for new records (if needed)
    #     #         'form_view_initial_mode': 'edit',  # Open form view in edit mode
    #     #         'default_move_type': 'out_receipt',
    #     #         'default_partner_id': self.partner_id.id,
    #     #         # 'default_analytic_account_id_2': analytic,
    #     #         # 'default_journal_id': receipt_journal,
    #     #         'default_invoice_line_ids': invoice_lines
    #     #     },
    #     # }
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Receipts',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.move',
    #         'domain': [('sale_id', '=', self.id)],
    #         'context': {
    #             'default_sale_id': self.id,
    #             'form_view_initial_mode': 'edit',
    #             'default_move_type': 'out_receipt',
    #             'default_partner_id': self.partner_id.id
    #         },
    #     }
    # analytic = self.analytic_account_id.id
    # receipt_journal = 16
    # return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Receipts',
    #         'view_mode': 'form',
    #         'res_model': 'account.move',
    #         'domain': [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)],
    #         # 'res_id': account_move.id,
    #         'context': {'default_move_type': 'out_receipt',
    #                     'default_partner_id': self.partner_id.id,
    #                     'default_sale_id': self.id,
    #                     # 'default_analytic_account_id_2': analytic,
    #                     # 'default_journal_id': receipt_journal,
    #                     # 'default_invoice_line_ids': default_order_lines
    #                     },
    #     }

    # def get_receipt(self):
    #     self.ensure_one()
    #
    #     # Search for an existing account move or prepare to create a new one
    #     account_move = self.env['account.move'].search(
    #         [('sale_id', '=', self.id), ('partner_id', '=', self.partner_id.id)], limit=1)
    #
    #     # Determine the currency
    #     currency_id = account_move.currency_id.id if account_move else self.env.ref('base.main_company').currency_id.id
    #
    #     # Prepare the invoice lines
    #     invoice_lines = [(0, 0, {
    #         'product_id': line.product_id.id,
    #         'price_unit': line.price_unit,
    #         'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
    #         'name': line.name,
    #         'quantity': line.product_uom_qty,
    #         'currency_id': currency_id,
    #
    #         # 'analytic_distribution': self.analytic_account_id.id
    #     }) for line in self.order_line]
    #     analytic = self.analytic_account_id.id
    #     # Create a new account move if one does not exist
    #     if not account_move:
    #         account_move = self.env['account.move'].create({
    #             'move_type': 'out_receipt',
    #             'partner_id': self.partner_id.id,
    #             'currency_id': currency_id,
    #             'sale_id': self.id,
    #             'journal_id': 16,  # Assuming 16 is your receipt journal ID
    #             'analytic_account_id_2': analytic,
    #             'line_ids': invoice_lines,
    #         })
    #
    #     # Return an action to open the form view of the created/found account move
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Receipts',
    #         'view_mode': 'form',
    #         'res_model': 'account.move',
    #         'res_id': account_move.id,
    #         'context': {'form_view_initial_mode': 'edit'},  # Open in edit mode if needed
    #     }
    #


class AccountMove(models.Model):
    _inherit = 'account.move'

    analytic_account_id_2 = fields.Many2one('account.analytic.account')
