/** @odoo-module */
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";

export class ClinicButton extends Component {
    static template = "pos_inherit.ClinicButton";

    setup() {
        this.pos = usePos();
    }

    get partner() {
        const order = this.pos.get_order();
        return order ? order.get_partner() : null;
    }

    get clinic(){
        const order= this.pos.get_order();
        return order ? order.get_clinic() : null;
    }
}

ProductScreen.addControlButton({
    component: ClinicButton,
    position: ["before", "SetFiscalPositionButton"],
    condition: function () {
        return true;
    },
});
