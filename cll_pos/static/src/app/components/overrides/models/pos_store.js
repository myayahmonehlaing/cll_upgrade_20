/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    getReceiptHeaderData(order) {
        return {
            ...super.getReceiptHeaderData(...arguments),
            partner: this.selectedOrder?.partner,
        };
    },
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.title = loadedData['res.partner.title'];
        this.parent_id = loadedData['res.partner.company'];
    }
});
