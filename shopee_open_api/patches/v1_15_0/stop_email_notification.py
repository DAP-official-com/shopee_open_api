import frappe


def execute():
    if not frappe.db.exists("Notification Settings", "shopee@example.com"):
        return
    notification_setting = frappe.get_doc("Notification Settings", "shopee@example.com")
    notification_setting.enable_email_notifications = False
    notification_setting.save()
