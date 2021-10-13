frappe.ui.form.on('Branch', {
	refresh: function (frm) {
		if (frm.doc.shopee_shop_id) {
			frm.add_custom_button('Refresh from Shopee', () => {
				frappe.call({
					method: 'shopee_open_api.apis.shop.reload_shop_details_from_shopee',
					args: {
						branch_name: frm.doc.name,
					},
					callback: function (r) {
						frm.refresh();
					},
				});
			});
		}
	},
});
