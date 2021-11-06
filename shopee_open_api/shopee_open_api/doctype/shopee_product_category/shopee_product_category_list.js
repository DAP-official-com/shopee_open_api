frappe.listview_settings['Shopee Product Category'] = {
	onload: function (listview) {
		this.add_button(['Import Categories'], 'success', async function () {
			frappe.call({
				method: 'shopee_open_api.apis.product_category.import_categories',
				callback: function (r) {
					frappe.msgprint(__('Categories imported successfully'));
				},
				error: function (e) {
					if (e.exc_type == 'NoShopAuthorizedError') {
						window.open('/app/branch', '_blank');
					}
				},
			});
		});
	},

	add_button(name, type, action, wrapper_class = '.page-actions') {
		const button = document.createElement('button');
		button.classList.add('btn', 'btn-' + type, 'btn-sm', 'ml-2');
		button.innerHTML = name;
		button.onclick = action;
		document.querySelector(wrapper_class).prepend(button);
	},
};
