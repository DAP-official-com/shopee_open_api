// Copyright (c) 2021, Dap Official and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shopee Product', {
	refresh: function (frm) {
		if (frm.doc.item == undefined) {
			frm.add_custom_button('Create New Item from This Product', () => {
				frappe.call({
					method: 'shopee_open_api.apis.product.create_new_item_and_add_to_product',
					args: {
						product_primary_key: frm.doc.name,
					},
					callback: function (r) {
						window.location.reload();
					},
				});
			});
		}

		frm.add_custom_button('Refresh from Shopee', () => {
			frappe.call({
				method: 'shopee_open_api.apis.product.reload_product_details_from_shopee',
				args: {
					product_primary_key: frm.doc.name,
				},
				callback: function (r) {
					frm.refresh();
				},
			});
		});
	},
});
