from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import ValidationError


class SubCategory(models.Model):
    _inherit = 'sale.order'

    flag = fields.Boolean('Flag')

    def create_receipt(self):
        self.flag = True
        receipt_vals = {
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'move_type': 'out_receipt',
            'sale_id': self.id,
            'invoice_line_ids':
                self.order_line.mapped(lambda line: (0, 0,
                                                     {'product_id': line.product_id.id,
                                                      'price_unit': line.price_unit,
                                                      'account_id': line.product_id.categ_id.property_account_income_categ_id.id,
                                                      'name': line.name,
                                                      'quantity': line.product_uom_qty,
                                                      'tax_ids': line.tax_id}))}
        receipt = self.env['account.move'].with_user(SUPERUSER_ID).create(receipt_vals)

        return receipt

    def get_receipt(self):
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
                                                                    }))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipts',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('sale_id', '=', self.id)],
            'context': {'default_move_type': 'out_receipt',
                        'default_partner_id': default_partner_id,
                        'default_invoice_line_ids': default_order_lines},
        }
