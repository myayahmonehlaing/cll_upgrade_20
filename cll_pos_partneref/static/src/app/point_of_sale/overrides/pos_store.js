/** @odoo-module */

import { patch } from "@web/core/utils/patch";

import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async selectRef() {
        const currentOrder = this.get_order();
        if (!currentOrder) {
            return;
        }
    
        const currentRef = currentOrder.get_ref();
        const { confirmed, payload: newRef } = await this.showTempScreen("RefListScreen", {
            ref: currentRef,
        });

        if (confirmed) {
            currentOrder.set_ref(newRef);
        }
    },

    async selectClinic() {
        const currentOrder = this.get_order();
        if (!currentOrder) {
            return;
        }

        const currentClinic = currentOrder.get_clinic();
        const { confirmed, payload: newClinic } = await this.showTempScreen("ClinicListScreen", {
            clinic: currentClinic,
        });

        if (confirmed) {
            currentOrder.set_clinic(newClinic);
        }
    }
})
