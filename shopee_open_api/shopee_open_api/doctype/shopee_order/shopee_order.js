// Copyright (c) 2021, Dap Official and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shopee Order', {
	refresh: function (frm) {
		if (frm.doc.sales_order == undefined) {
			frm.add_custom_button('Create Sales Order', () => {
				frappe.call({
					method: 'shopee_open_api.apis.order.create_sales_order_from_shopee_order',
					args: {
						order_sn: frm.doc.name,
					},
					callback: function (r) {
						frappe.set_route('Form', 'Sales Order', r.message.name);
					},
				});
			});
		}

		frm.add_custom_button('Refresh from Shopee', () => {
			frappe.call({
				method: 'shopee_open_api.apis.order.reload_order_details_from_shopee',
				args: {
					shop_id: frm.doc.shopee_shop,
					order_sn: frm.doc.order_sn,
				},
				callback: function (r) {
					frm.refresh();
				},
			});
		});
	},
});
