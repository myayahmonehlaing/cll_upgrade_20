/** @odoo-module */
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { patch } from "@web/core/utils/patch";
patch(PartnerDetailsEdit.prototype, {
    setup() {
        super.setup();
        this.intFields.push("title");
        this.intFields.push("parent_id");
        this.changes.date_of_birth = this.props.partner.date_of_birth || '';
        this.changes.age = this.props.partner.age || '';
        this.changes.gender_id = this.props.partner.gender_id || '';
        this.changes.title =
            this.props.partner.title && this.props.partner.title[0];
        this.changes.parent_id =
            this.props.partner.parent_id && this.props.partner.parent_id[0];
    },
    async saveChanges() {
        if (
            (!this.props.partner.date_of_birth && !this.changes.date_of_birth) ||
            this.changes.date_of_birth === ""
        ) {
            this.changes.date_of_birth = false
        }

        if (
            (!this.props.partner.gender_id && !this.changes.gender_id) ||
            this.changes.gender_id === ""
        ) {
            this.changes.gender_id = false
        }

        if (
            (!this.props.partner.title && !this.changes.title) ||
            this.changes.title === ""
        ) {
            this.changes.title = false
        } else {
            this.changes.title = [parseInt(this.changes.title)];
        }

        if (
            (!this.props.partner.parent_id && !this.changes.parent_id) ||
            this.changes.parent_id === ""
        ) {
            this.changes.parent_id = false
        } else {
            this.changes.parent_id = [parseInt(this.changes.parent_id)];
        }
        await super.saveChanges();
    },
});
