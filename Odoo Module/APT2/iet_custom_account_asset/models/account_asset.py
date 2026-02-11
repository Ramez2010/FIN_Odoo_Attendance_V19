from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.tools import float_is_zero

DAYS_PER_MONTH = 30


class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'

    method_period = fields.Selection([('1', 'Months'), ('12', 'Years'), ('1/30', 'Days')],
                                     string='Number of Months in a Period',
                                     help="The amount of time between two depreciations")


class AccountAssetCustom(models.Model):
    _inherit = 'account.asset'

    method_period = fields.Selection([('1', 'Months'), ('12', 'Years'), ('1/30', 'Days')],
                                     string='Number of Months in a Period',
                                     readonly=True, default='12',
                                     states={'draft': [('readonly', False)], 'model': [('readonly', False)]},
                                     help="The amount of time between two depreciations")

    @api.depends('method_number', 'method_period', 'prorata_computation_type')
    def _compute_lifetime_days(self):
        for asset in self:
            if asset.method_period == '1/30':
                period_days = 1
            elif asset.method_period == '1':
                period_days = DAYS_PER_MONTH
            elif asset.method_period == '12':
                period_days = 12 * DAYS_PER_MONTH
            else:
                raise ValueError("Invalid method_period value")

            if asset.prorata_computation_type == 'daily_computation':
                asset.asset_lifetime_days = (asset.prorata_date + relativedelta(
                    months=asset.method_number) - asset.prorata_date).days
            else:
                asset.asset_lifetime_days = period_days * asset.method_number

    def _recompute_board(self, date=None):
        self.ensure_one()
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(
            lambda mv: mv.state == 'posted' and not mv.asset_value_change
        ).sorted(key=lambda mv: (mv.date, mv.id))

        imported_amount = self.already_depreciated_amount_import
        residual_amount = self.value_residual
        if not posted_depreciation_move_ids:
            residual_amount += imported_amount
        residual_declining = residual_amount

        days_already_depreciated = sum(posted_depreciation_move_ids.mapped('asset_number_days'))
        days_already_added = sum(
            [(mv.date - mv.asset_depreciation_beginning_date).days + 1 for mv in posted_depreciation_move_ids])

        if self.method_period == '1/30':
            period_days = 1
        elif self.method_period == '1':
            period_days = DAYS_PER_MONTH
        elif self.method_period == '12':
            period_days = 12 * DAYS_PER_MONTH
        else:
            raise ValueError("Invalid method_period value")

        start_depreciation_date = self.paused_prorata_date + relativedelta(days=days_already_added)

        depreciation_move_values = []
        if not float_is_zero(self.value_residual, precision_rounding=self.currency_id.rounding):
            for i in range(self.method_number):
                period_end_depreciation_date = start_depreciation_date + relativedelta(days=period_days - 1)

                days = (period_end_depreciation_date - start_depreciation_date).days + 1
                amount = (residual_declining / self.asset_lifetime_days) * days

                if not posted_depreciation_move_ids:

                    if abs(imported_amount) <= abs(amount):
                        amount -= imported_amount
                        imported_amount = 0
                    else:
                        imported_amount -= amount
                        amount = 0

                if not float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    depreciation_move_values.append(self.env['account.move']._prepare_move_for_asset_depreciation({
                        'amount': amount,
                        'asset_id': self,
                        'depreciation_beginning_date': start_depreciation_date,
                        'date': period_end_depreciation_date,
                        'asset_number_days': days,
                    }))

                start_depreciation_date = period_end_depreciation_date + relativedelta(days=1)

        return depreciation_move_values
