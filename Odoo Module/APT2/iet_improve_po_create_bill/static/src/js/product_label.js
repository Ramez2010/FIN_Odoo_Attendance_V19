import { SaleOrderLineProductField } from "@sale/js/sale_product_field";
import { patch } from "@web/core/utils/patch";

patch(SaleOrderLineProductField.prototype, {
    get label() {
        return this.props.record.data.name ;
    },

    parseLabel(value) {
        return value ? value : "";
    },


});