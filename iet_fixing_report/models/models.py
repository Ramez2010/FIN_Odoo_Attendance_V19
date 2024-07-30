from odoo import models, fields, api, osv
from odoo.addons.web.controllers.utils import clean_action
from psycopg2 import sql
from odoo.addons.account_reports.models.account_analytic_report import AccountMoveLine


def _where_calc(self, domain, active_test=True):
    print("dDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD")
    """ In case we need an analytic column in an account_report, we shadow the account_move_line table
    with a temp table filled with analytic data, that will be used for the analytic columns.
    We do it in this function to only create and fill it once for all computations of a report.
    The following analytic columns and computations will just query the shadowed table instead of the real one.
    """
    query = super()._where_calc(domain, active_test)
    if self.env.context.get('account_report_analytic_groupby'):
        self.env['account.report']._prepare_lines_for_analytic_groupby()
        query._tables['account_move_line'] = 'analytic_temp_account_move_line'
    return query


AccountMoveLine._where_calc = _where_calc