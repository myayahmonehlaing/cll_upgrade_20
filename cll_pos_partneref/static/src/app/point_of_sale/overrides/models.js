/** @odoo-module */

import { patch } from "@web/core/utils/patch";

import { Order } from "@point_of_sale/app/store/models";

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.ref = null;
        this.clinic = null;
    },
    export_as_JSON() {
        const json=super.export_as_JSON(...arguments)
        json['ref'] = this.ref ? this.ref : false;
        json['clinic'] = this.clinic ? this.clinic : false;
        return json;
    },

    init_from_JSON(json) {
        // this function is overrided for assigning json value to this
        super.init_from_JSON(...arguments);
        // console.log(json)
        this.ref = json.ref_id ? json.ref_id : false;
        this.clinic = json.clinic_id ? json.clinic_id : false;
    },
    /* ---- Ref ---- */
    // the ref related to the current order.
    set_ref(ref) {
        this.assert_editable();
        this.ref = ref;
    },

    get_ref() {
        return this.ref;
    },

    get_ref_name() {
        const ref = this.ref;
        return ref ? ref.name : "";
    },

    /* ---- Clinic ---- */
    // the clinc related to the current order.
    set_clinic(clinic) {
        this.assert_editable();
        this.clinic = clinic;
    },

    get_clinic() {
        return this.clinic;
    },

    get_clinic_name() {
        const clinic = this.clinic;
        return clinic ? clinic.name : "";
    }
})
