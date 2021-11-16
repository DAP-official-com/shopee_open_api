import frappe


def execute():
    if frappe.db.exists(
        {"doctype": "Accounting Dimension", "document_type": "Shopee Shop"}
    ):
        return

    dimension = frappe.new_doc("Accounting Dimension")
    dimension.document_type = "Shopee Shop"
    dimension.insert()
