/** @odoo-module **/

import { t, Component, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";
import { localization } from "@web/core/l10n/localization";
import { formatDate, deserializeDate } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";

import { formatMonetary } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";


class AccountAdvancePopOver extends Component {
    props = useProps({
        "*": t.any().optional(),
    });
}
AccountAdvancePopOver.template = "cll_account.AccountAdvancePopOver";


export class AccountAdvanceField extends Component {
    props = useProps({
        ...standardFieldProps,
    });

    setup() {
        const position = localization.direction === "rtl" ? "bottom" : "left";
        this.popover = usePopover(AccountAdvancePopOver, { position });
        this.orm = useService("orm");
        this.action = useService("action");
    }

    getInfo() {
        const info = this.props.record.data[this.props.name] || {
            content: [],
            title: "",
            advance_balance: 0.0,
            move_id: this.props.record.resId,
        };

        for (const [key, value] of Object.entries(info.content)) {
            value.index = key;
            value.amount_formatted = formatMonetary(value.amount, {
                currencyId: value.currency_id,
            });

            if (value.date) {
                value.formattedDate = formatDate(deserializeDate(value.date));
            }
        }

        return {
            lines: info.content,
            title: info.title,
            advance_balance: info.advance_balance,
            moveId: info.move_id,
        };
    }

    onInfoClick(ev, line) {
        this.popover.open(ev.currentTarget, {
            title: _t("Vendor Advance Info"),
            ...line,
            _onOpenMove: this.openMove.bind(this),
        });
    }

    async openMove(moveId) {
        const action = await this.orm.call(
            this.props.record.resModel,
            "action_open_advance_move",
            [moveId],
            {}
        );
        this.action.doAction(action);
    }
}

AccountAdvanceField.template = "cll_account.AccountAdvanceField";

export const accountAdvanceField = {
    component: AccountAdvanceField,
    supportedTypes: ["char"],
};

registry.category("fields").add("advance", accountAdvanceField);