/** @odoo-module */

import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(AccountReportFilters.prototype, {

    get analyticPlans() {
        return this.controller.cachedFilterOptions.available_analytic_plans || [];
    },

    isPlanSelected(planId) {
        const selectedPlans = this.controller.cachedFilterOptions.analytic_plans_groupby || [];
        return selectedPlans.includes(planId);
    },

    async onAnalyticFilterClick(filterKey, optionId = null) {
        // 1. Analytic Plans
        if (filterKey === 'analytic_plans_groupby') {
            let currentIds = [...(this.controller.cachedFilterOptions.analytic_plans_groupby || [])];
            if (currentIds.includes(optionId)) {
                currentIds = currentIds.filter(id => id !== optionId);
            } else {
                currentIds.push(optionId);
            }
            await this.filterClicked({
                optionKey: 'analytic_plans_groupby',
                optionValue: currentIds,
                reload: true
            });
        }

        // 2. Analytic Accounts (Popup)
        if (filterKey === 'analytic_accounts_groupby') {
            this.dialog.add(SelectCreateDialog, {
                resModel: 'account.analytic.account',
                title: _t('Select Analytic Accounts'),
                multiSelect: true,
                noCreate: true,
                domain: [],
                onSelected: async (resIds) => {
                    await this.filterClicked({
                        optionKey: 'analytic_accounts_groupby',
                        optionValue: resIds,
                        reload: true
                    });
                }
            });
        }
    }
});