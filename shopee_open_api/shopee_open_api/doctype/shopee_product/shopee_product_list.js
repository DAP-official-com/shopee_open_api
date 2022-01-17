// Copyright (c) 2021, Dap Official and contributors
// For license information, please see license.txt

frappe.listview_settings['Shopee Product'] = {
	onload: function (listview) {
		this.add_button(['Refresh products'], 'info', function () {
			frappe.call({
				method: 'shopee_open_api.apis.product.sync_products',
				callback: function (r) {
					return;
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
