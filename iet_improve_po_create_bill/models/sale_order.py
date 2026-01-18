from odoo import models, api,fields

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("order_id", "product_id")
    def _onchange_set_analytic_distribution_from_so(self):
        for line in self:
            order = line.order_id
            if (
                order.analytic_account_id
                and not line.analytic_distribution
            ):
                line.analytic_distribution = {
                    str(order.analytic_account_id.id): 100
                }

    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)

    @api.depends('product_id', 'linked_line_id', 'linked_line_ids')
    def _compute_name(self):
        for line in self:
            if not line.product_id and not line.is_downpayment:
                continue

            lang = line.order_id._get_lang()
            if lang != self.env.lang:
                line = line.with_context(lang=lang)

            if line.product_id:
                line.name = ''
                print(f'Product {line.product_id.name}')
                print(f'Product {line.name}')
                continue

            if line.is_downpayment:
                line.name = line._get_downpayment_description()

    @api.onchange("product_id")
    def _onchange_product_id_clear_name(self):
        for line in self:
            if line.product_id and not line.is_downpayment:
                line.name = False
                print(f'line,anme from on change==>{line.name}')

    def create(self, vals_list):
        for vals in vals_list:
            print(f"Manual name entered: {vals_list}")
            print(f"Manual name entered: {vals.get('name')}")
        return super().create(vals_list)