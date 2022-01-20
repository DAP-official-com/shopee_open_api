import frappe


def execute():
    new_warehouse = frappe.get_doc(
        {
            "doctype": "Customer Group",
            "customer_group_name": "Shopee",
            "parent_customer_group": "All Customer Groups",
        }
    )
    new_warehouse.insert()
