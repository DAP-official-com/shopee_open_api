frappe.listview_settings["Branch"] = {

	onload: function(listview) {
		this.add_button(["Add shopee as a new branch"], "default", function() { 
			// can I add something here?
			frappe.call({
				method: "shopee_open_api.auth.get_authorize_url",
				callback: function(r) {
					let authorizeUrl = r['message'];
					window.open(authorizeUrl, "_self");
				}
			})
		})
	},

	add_button(name, type, action, wrapper_class=".page-actions") {
		const button = document.createElement("button");
		button.classList.add("btn", "btn-" + type, "btn-sm", "ml-2");
		button.innerHTML = name;
		button.onclick = action;
		document.querySelector(wrapper_class).prepend(button);
	},
};