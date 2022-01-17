// Copyright (c) 2016, Dap Official and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports['Shopee Business Insights'] = {
	filters: [
		{
			fieldname: 'date_start',
			label: 'Date Start',
			fieldtype: 'Date',
			//Note the following default attribute, which contains an API call
			// default: frappe.datetime.get_today(),
		},
		{
			fieldname: 'date_end',
			label: 'Date End',
			fieldtype: 'Date',
			//Note the following default attribute, which contains an API call
			// default: frappe.datetime.get_today(),
		},
		{
			fieldname: 'order_status',
			label: 'Order Status',
			fieldtype: 'Link',
			options: 'Shopee Order Status',
		},
		{
			fieldname: 'timeline_group',
			label: 'Date Group',
			fieldtype: 'Select',
			default: 'Monthly',
			options: 'Daily\nMonthly\nAnnually',
		},
	],
};
