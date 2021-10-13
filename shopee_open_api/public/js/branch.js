frappe.ui.form.on('Branch', {
    refresh: function(frm) {
        if (frm.doc.shopee_shop_id) {
            frm.add_custom_button('Disconnect from shopee', () => {
                frappe.call({
                    method: "shopee_open_api.auth.get_unauthorize_url",
                    callback: function(r) {
                        let unauthorizeUrl = r['message'];
                        window.open(unauthorizeUrl, "_self");
                    }
                })
            })
        }
    }
});