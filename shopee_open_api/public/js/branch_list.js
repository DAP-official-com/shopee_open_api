frappe.listview_settings['Branch'] = {
	onload: function (listview) {
		this.add_button(['Add from Shopee'], 'warning', function () {
			frappe.call({
				method: 'shopee_open_api.auth.get_authorize_url',
				callback: function (r) {
					let authorizeUrl = r['message'];
					window.open(authorizeUrl, '_self');
				},
			});
		});

		this.add_button(['Remove Shopee Branch'], 'danger', function () {
			frappe.call({
				method: 'shopee_open_api.auth.get_unauthorize_url',
				callback: function (r) {
					let unauthorizeUrl = r['message'];
					window.open(unauthorizeUrl, '_self');
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
