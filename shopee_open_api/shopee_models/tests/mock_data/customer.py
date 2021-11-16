import frappe

customer_data = {
    "customer_type": "Individual",
    "customer_group": "Individual",
    "customer_name": "Fakefirstname Fakelastname",
    "territory": frappe.db.get_default("Country"),
    "username": "shopee_username",
    "user_id": "shopee_user_id",
    "shopee_user_id": "shopee_user_id",
    "mobile_no": "66888888888",
}
