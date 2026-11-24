/** @odoo-module **/

import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";

patch(PartnerListScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.selectRef = this.props.ref;
        this.state.selectClinic = this.props.clinic;
    }
    
});
