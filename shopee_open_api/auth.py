import frappe
import json
import hmac, time, requests, hashlib
from .python_shopee import pyshopee2


PARTNER_ID = frappe.db.get_single_value("Shopee API Settings", "partner_id")
PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")
REDIRECT_URL = "http://localhost:8000/api/method/shopee_open_api.auth.authenticate_after_authorization"

client = pyshopee2.Client(
    shop_id=0,
    partner_id=PARTNER_ID,
    partner_key=PARTNER_KEY,
    redirect_url=REDIRECT_URL,
    test_env=True,
)


@frappe.whitelist()
def authorize():

    url = client.shop_authorization(redirect_url=REDIRECT_URL)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url


@frappe.whitelist()
def authenticate_after_authorization():

    timest = int(time.time())
    host = "https://partner.test-stable.shopeemobile.com"
    path = "/api/v2/auth/token/get"

    code = frappe.request.args.getlist("code")[0]
    shop_id = int(frappe.request.args.getlist("shop_id")[0])

    base_string = "%s%s%s" % (PARTNER_ID, path, timest)

    sign = hmac.new(
        PARTNER_KEY.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    body = {
        "code": code,
        "shop_id": shop_id,
        "partner_id": PARTNER_ID,
    }

    url = (
        host + path + "?partner_id=%s&timestamp=%s&sign=%s" % (PARTNER_ID, timest, sign)
    )

    headers = {"Content-Type": "application/json"}
    r = requests.post(url, json=body, headers=headers)

    content = r.json()
    access_token = content["access_token"]

    path = "/api/v2/shop/get_shop_info"
    base_string = "%s%s%s%s%s" % (PARTNER_ID, path, timest, access_token, shop_id)

    sign = hmac.new(
        PARTNER_KEY.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    url = (
        host
        + path
        + "?partner_id=%s&timestamp=%s&access_token=%s&shop_id=%s&sign=%s"
        % (PARTNER_ID, timest, access_token, shop_id, sign)
    )

    r = requests.get(url)
    print(r.json())

    return content
