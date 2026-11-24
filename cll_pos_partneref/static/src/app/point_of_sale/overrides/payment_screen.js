// /** @odoo-module */

// import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
// import { patch } from "@web/core/utils/patch";

// patch(PaymentScreen.prototype, {
//     async selectRef(isEditMode = false, missingFields = []) {
//         // IMPROVEMENT: This code snippet is repeated multiple times.
//         // Maybe it's better to create a function for it.
//         const currentRef = this.currentOrder.get_ref();
//         const partnerScreenProps = { ref: currentRef };
//         if (isEditMode && currentRef) {
//             partnerScreenProps.editModeProps = true;
//             partnerScreenProps.missingFields = missingFields;
//         }
//         const { confirmed, payload: newPartner } = await this.pos.showTempScreen(
//             "PartnerListScreen",
//             partnerScreenProps
//         );
//         if (confirmed) {
//             this.currentOrder.set_ref(newPartner);
//         }
//     }
// });
