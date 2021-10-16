// Copyright (c) 2021, Dap Official and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shopee Shop', {
	refresh: function (frm) {
		frm.add_custom_button('Refresh from Shopee', () => {
			frappe.call({
				method: 'shopee_open_api.apis.shop.reload_shop_details_from_shopee',
				args: {
					shop_id: frm.doc.shop_id,
				},
				callback: function (r) {
					frm.refresh();
				},
			});
		});
	},
});
