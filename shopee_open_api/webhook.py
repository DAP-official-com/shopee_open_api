import frappe
import json
import hmac, time, requests, hashlib


PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")


@frappe.whitelist(allow_guest=True)
def listener():

    authorization_header = frappe.request.headers.get("Authorization")
    host = frappe.request.headers.get("Host")
    path = "/api/method/shopee_open_api.webhook.listener"
    raw_body = frappe.request.data.decode()

    base_string = host + path + "|" + raw_body

    cal_auth = hmac.new(
        PARTNER_KEY.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # print(f"base_string: {base_string}")
    # print(f"cal_auth: {cal_auth}")
    # print(f"auth_header: {authorization_header}")

    return
