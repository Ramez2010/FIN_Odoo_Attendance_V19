from odoo import models, fields, api, _
from odoo.tools import SQL
from odoo.exceptions import UserError


class IetFinancialReport(models.AbstractModel):
    _inherit = 'account.report'

    filter_analytic_groupby = fields.Boolean(
        string="Analytic Group By",
        default=False,
        readonly=False, store=True, depends=['root_report_id'],
    )

    # -------------------------------------------------------------------------
    # 1. ترتيب الأولويات (Sequence)
    # -------------------------------------------------------------------------
    def _get_options_initializers_forced_sequence_map(self):
        sequence_map = super()._get_options_initializers_forced_sequence_map()
        sequence_map[self._init_options_analytic_groupby] = 995
        return sequence_map


    def _init_options_analytic_groupby(self, options, previous_options=None):
        if not self.filter_analytic_groupby:
            return

        if not self.env.user.has_group('analytic.group_analytic_accounting'):
            return

        options['analytic_groupby'] = True
        options['include_analytic_without_aml'] = (previous_options or {}).get('include_analytic_without_aml', False)

        available_plans = self.env['account.analytic.plan'].search([])
        options['available_analytic_plans'] = [{'id': p.id, 'name': p.name} for p in available_plans]

        prev_analytics = (previous_options or {}).get('analytic_accounts_groupby', [])
        if isinstance(prev_analytics, int): prev_analytics = [prev_analytics]
        analytic_ids = [int(x) for x in prev_analytics]
        selected_analytics = self.env['account.analytic.account'].with_context(active_test=False).search(
            [('id', 'in', analytic_ids)])
        options['analytic_accounts_groupby'] = selected_analytics.ids

        prev_plans = (previous_options or {}).get('analytic_plans_groupby', [])
        if isinstance(prev_plans, int): prev_plans = [prev_plans]
        plan_ids = [int(x) for x in prev_plans]
        options['analytic_plans_groupby'] = plan_ids

        self._create_column_analytic(options)

    def _create_column_analytic(self, options):
        analytic_headers = []

        if options.get('analytic_plans_groupby'):
            plans = self.env['account.analytic.plan'].browse(options['analytic_plans_groupby'])
            for plan in plans:
                child_accounts = self.env['account.analytic.account'].search([('plan_id', 'child_of', plan.id)])
                if not child_accounts:
                    continue
                analytic_headers.append({
                    'name': plan.name,
                    'forced_options': {
                        'analytic_groupby_option': True,
                        'analytic_accounts_list': tuple(child_accounts.ids),
                    }
                })

        if options.get('analytic_accounts_groupby'):
            accounts = self.env['account.analytic.account'].browse(options['analytic_accounts_groupby'])
            for account in accounts:
                analytic_headers.append({
                    'name': account.name,
                    'forced_options': {
                        'analytic_groupby_option': True,
                        'analytic_accounts_list': (account.id,),
                    }
                })

        if analytic_headers and options.get('column_headers'):
            options['column_headers'][0].extend(analytic_headers)

    def _init_options_filters(self, options, previous_options=None):
        super()._init_options_filters(options, previous_options)
        if options.get('analytic_groupby'):
            options['filters']['show_analytic_groupby'] = True

    def _get_report_query(self, options, date_scope, domain=None):
        query = super()._get_report_query(options, date_scope, domain)

        if options.get('analytic_groupby_option'):
            shadow_aml = self._get_analytic_shadow_table_sql(options)
            query._tables['account_move_line'] = shadow_aml

            allowed_account_ids = options.get('analytic_accounts_list')
            if allowed_account_ids:
                query.add_where(SQL(
                    "account_move_line.analytic_line_account_id IN %s",
                    tuple(allowed_account_ids)
                ))

        return query

    def _get_analytic_shadow_table_sql(self, options):
        return SQL("""
            (
                SELECT
                    aal.id,
                    aal.general_account_id AS account_id,
                    aal.date,
                    aal.company_id,
                    aal.journal_id,
                    aal.partner_id,
                    'posted' AS parent_state,
                    'product' AS display_type,

                    -aal.amount AS balance,
                    -aal.amount AS amount_currency,
                    CASE WHEN aal.amount < 0 THEN ABS(aal.amount) ELSE 0 END AS debit,
                    CASE WHEN aal.amount > 0 THEN aal.amount ELSE 0 END AS credit,

                    aal.account_id AS analytic_line_account_id,

                    jsonb_build_object(aal.account_id::text, 100) AS analytic_distribution,

                    aal.currency_id,
                    real_aml.move_id AS move_id

                FROM account_analytic_line aal
                LEFT JOIN account_move_line real_aml ON aal.move_line_id = real_aml.id

                WHERE aal.general_account_id IS NOT NULL
                  AND (%(include_no_aml)s OR aal.move_line_id IS NOT NULL)
            )
        """, include_no_aml=options.get('include_analytic_without_aml', False))


    def action_audit_cell(self, options, params):
        column_group_options = self._get_column_group_options(options, params['column_group_key'])

        if not column_group_options.get('analytic_groupby_option'):
            return super().action_audit_cell(options, params)

        report_line = self.env['account.report.line'].browse(params['report_line_id'])
        expression = report_line.expression_ids.filtered(lambda x: x.label == params['expression_label'])
        aml_domain = self._get_audit_line_domain(column_group_options, expression, params)

        aal_domain = []
        analytic_account_ids = column_group_options.get('analytic_accounts_list', [])

        for leaf in aml_domain:
            if len(leaf) == 1:
                aal_domain.append(leaf)
                continue
            field, operator, value = leaf
            if field == 'account_id':
                aal_domain.append(('general_account_id', operator, value))
            elif field == 'analytic_distribution':
                pass
            elif field in self.env['account.analytic.line']._fields:
                aal_domain.append(leaf)

        if analytic_account_ids:
            aal_domain.append(('account_id', 'in', analytic_account_ids))

        return {
            'type': 'ir.actions.act_window',
            'name': _("Analytic Lines"),
            'res_model': 'account.analytic.line',
            'views': [[False, 'list'], [False, 'form']],
            'domain': aal_domain,
            'context': {**self.env.context, 'active_test': False},
        }