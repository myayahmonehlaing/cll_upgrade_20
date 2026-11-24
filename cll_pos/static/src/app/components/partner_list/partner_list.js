/** @odoo-module */

import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
patch(PartnerListScreen.prototype, {
    createPartner() {
        super.createPartner(...arguments);
        this.state.editModeProps.partner.title = [
            this.pos.title[0].id,
            this.pos.title[0].name,
        ];
        // this.state.editModeProps.partner.parent_id = [
        //     this.pos.parent_id[0].id,
        //     this.pos.parent_id[0].name,
        // ];
    }
}
)
