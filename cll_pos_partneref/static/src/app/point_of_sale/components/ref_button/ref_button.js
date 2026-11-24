/** @odoo-module */
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";

export class RefButton extends Component {
    static template = "pos_inherit.RefButton";

    setup() {
        this.pos = usePos();
    }

    get partner() {
        const order = this.pos.get_order();
        return order ? order.get_partner() : null;
    }

    get ref(){
        const order= this.pos.get_order();
        return order ? order.get_ref() : null;
    }
}

ProductScreen.addControlButton({
    component: RefButton,
    position: ["after", "SetFiscalPositionButton"],
    condition: function () {
        return true;
    },
});
