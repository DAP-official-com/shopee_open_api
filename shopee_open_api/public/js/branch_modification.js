(function () {
    'use strict';

    frappe.ui.form.on('Branch', {
        refresh: function(frm) {
            if (frm.doc.shopee_shop_id) {
                frm.add_custom_button('Disconnect from shopee', function () {
                    frappe.call({
                        method: "shopee_open_api.auth.get_unauthorize_url",
                        callback: function(r) {
                            var unauthorizeUrl = r['message'];
                            window.open(unauthorizeUrl, "_self");
                        }
                    });
                });
            }
        }
    });

    frappe.listview_settings["Branch"] = {

    	onload: function(listview) {
    		this.add_button(["Add shopee as a new branch"], "default", function() { 
    			// can I add something here?
    			frappe.call({
    				method: "shopee_open_api.auth.get_authorize_url",
    				callback: function(r) {
    					var authorizeUrl = r['message'];
    					window.open(authorizeUrl, "_self");
    				}
    			});
    		});
    	},

    	add_button: function add_button(name, type, action, wrapper_class) {
    		if ( wrapper_class === void 0 ) wrapper_class=".page-actions";

    		var button = document.createElement("button");
    		button.classList.add("btn", "btn-" + type, "btn-sm", "ml-2");
    		button.innerHTML = name;
    		button.onclick = action;
    		document.querySelector(wrapper_class).prepend(button);
    	},
    };

}());
//# sourceMappingURL=branch_modification.js.map
