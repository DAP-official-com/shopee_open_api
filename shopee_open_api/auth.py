import frappe
import json
import hmac, time, requests, hashlib


@frappe.whitelist()
def authenticate_after_authorization():

    timest = int(time.time())
    host = "https://partner.test-stable.shopeemobile.com"
    path = "/api/v2/auth/token/get"
    partner_id = frappe.db.get_single_value("Shopee API Settings", "partner_id")
    partner_key = frappe.db.get_single_value("Shopee API Settings", "partner_key")

    code = frappe.request.args.getlist("code")[0]
    shop_id = int(frappe.request.args.getlist("shop_id")[0])
    base_string = "%s%s%s" % (partner_id, path, timest)
    sign = hmac.new(
        partner_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    body = {
        "code": code,
        "shop_id": shop_id,
        "partner_id": partner_id,
    }

    url = (
        host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (partner_id, timest, sign)
    )

    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=body, headers=headers)

    print(r.json())
