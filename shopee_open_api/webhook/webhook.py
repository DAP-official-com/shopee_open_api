import frappe
import json
import hmac, time, requests, hashlib
from .router import get_webhook_handler
import traceback


@frappe.whitelist(allow_guest=True)
def listener():

    PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")

    authorization_header = frappe.request.headers.get("Authorization")
    host = frappe.request.headers.get("Host")
    path = "/api/method/shopee_open_api.webhook.listener"
    raw_body = frappe.request.data.decode()

    base_string = host + path + "|" + raw_body

    cal_auth = hmac.new(
        PARTNER_KEY.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    data = json.loads(frappe.request.data)

    ## See all webhook codes here https://open.shopee.com/documents?module=87&type=2&id=63&version=2

    webhook_code = data.get("code", False)

    try:
        frappe.set_user("shopee@example.com")
        get_webhook_handler(webhook_code)(data)
    except:
        shopee_error = frappe.new_doc("Shopee Order Update Error")
        shopee_error.raw_data = str(data)
        shopee_error.error = str(traceback.format_exc())
        shopee_error.insert(ignore_permissions=True)
        frappe.db.commit()
        raise

    return
