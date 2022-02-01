import frappe


def execute():
    shopee_shop_ids = frappe.get_all("Shopee Shop", pluck="name")
    shopee_shop_documents = [
        frappe.get_doc("Shopee Shop", name) for name in shopee_shop_ids
    ]
    for shop in shopee_shop_documents:
        shop.create_receivable_account()
