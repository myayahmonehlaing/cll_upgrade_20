/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { AccountReportFilters } from "@account_reports/components/account_report/filters/filters";

patch(AccountReportFilters.prototype, {
    getMultiRecordSelectorProps(resModel, optionKey) {
        return {
            resModel,
            resIds: this.controller.cachedFilterOptions[optionKey],
            update: (resIds) => {
                this.filterClicked({
                    optionKey: optionKey,
                    optionValue: resIds,
                    reload: true,
                });
            },
            context: {
                analytic_groupby_plan_name: true,
            },
        };
    },
});
