frappe.listview_settings['Shopee Order'] = {
	onload: function (listview) {
		this.add_button(['Import Orders'], 'success', function () {
			d.show();
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

let d = new frappe.ui.Dialog({
	title: 'Import New Order',
	fields: [
		{
			label: 'Shop Id',
			fieldname: 'shop_id',
			fieldtype: 'Link',
			options: 'Shopee Shop',
			reqd: 1,
		},
		{
			label: 'Order Id(s)',
			fieldname: 'order_sn',
			fieldtype: 'Data',
			reqd: 1,
		},
	],
	primary_action_label: 'Import',
	primary_action(values) {
		frappe.call({
			method: 'shopee_open_api.apis.order.reload_order_details_from_shopee',
			args: {
				shop_id: values.shop_id,
				order_sn: values.order_sn,
			},
			callback: function (r) {
				if (r.message.message == 'ok') {
					frappe.msgprint(__('Order imported successfully'));
					d.hide();
				}
			},
		});
	},
});
