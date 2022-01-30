import frappe


def execute():
    try:
        new_user = frappe.new_doc("User")
        new_user.email = "shopee@example.com"
        new_user.first_name = "Shopee"
        new_user.insert()
        new_user.add_roles(
            "Sales User",
            "Accounts User",
            "System Manager",
        )
    except frappe.exceptions.OutgoingEmailError:
        pass
