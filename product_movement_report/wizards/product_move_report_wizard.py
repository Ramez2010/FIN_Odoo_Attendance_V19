from datetime import datetime, time
from odoo import fields, models


class ProductMoveReportWizard(models.TransientModel):
    _name = 'product.move.report.wizard'
    _description = "product.move.report.wizar"
    start_date = fields.Date(
        string='Start Date',
        required=False,
    )
    end_date = fields.Date(
        string='End Date',
        required=False,
    )

    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=False,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=False,
    )

    def generate_report(self):
        product_opening_balance = sum(self.env['stock.valuation.layer'].search(
            [
                ('create_date', '<=',
                 datetime.combine(date=self.start_date, time=time.max)),
                ('product_id', '=', self.product_id.id),
            ]).mapped('quantity'))
        product_moves = self.env['stock.move.line'].search(
            [
                '&',
                ('product_id', '=', self.product_id.id),
                '|',
                ('location_id', '=', self.location_id.id),
                ('location_dest_id', '=', self.location_id.id),
                '&',
                ('date', '<=',
                 datetime.combine(date=self.end_date, time=time.max)),
                ('date', '>=',
                 datetime.combine(date=self.start_date, time=time.max)),
            ],
            order='date',
        )
        flat_product_moves = [{
            'move_type':
            'in' if self.location_id == move.location_dest_id else 'out',
            'date':
            move.date,
            'operation_type':
            move.picking_code,
            'reference':
            move.reference,
            'qty':
            move.qty_done,
        } for move in product_moves]
        data = {
            'form': self.read()[0],
            'product_moves': flat_product_moves,
            'opening_balance': product_opening_balance,
        }
        return self.env.ref(
            'product_movement_report.product_moves_report_action'
        ).report_action(self, data=data)
