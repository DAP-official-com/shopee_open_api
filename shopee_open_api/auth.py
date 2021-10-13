import frappe
import time
from datetime import datetime
from shopee_open_api.utils.client import get_shopless_client

PARTNER_ID = frappe.db.get_single_value("Shopee API Settings", "partner_id")
PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")

UNAUTHORIZE_REDIRECT_URL = (
    f"{frappe.utils.get_url()}/api/method/shopee_open_api.auth.unauthorize_callback"
)

client = get_shopless_client()


@frappe.whitelist()
def authorize():

    url = client.shop_authorization(redirect_url=client.redirect_url)

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url


@frappe.whitelist()
def authorize_callback():

    code = frappe.request.args.getlist("code")[0]
    shop_id = int(frappe.request.args.getlist("shop_id")[0])

    client.code = code
    client.shop_id = shop_id
    client.get_token()

    shop_profile = client.shop.get_profile()["response"]
    shop_profile.update(client.shop.get_shop_info())

    shopee_branch_exists = frappe.db.exists(
        {"doctype": "Branch", "shopee_shop_id": shop_id}
    )

    if not shopee_branch_exists:

        doc = frappe.new_doc("Branch")
        doc.branch = shop_profile["shop_name"]
        doc.shopee_shop_id = shop_id
        doc.shopee_shop_logo = shop_profile["shop_logo"]
        doc.shopee_shop_status = shop_profile["status"]
        doc.shopee_shop_description = shop_profile["description"]
        doc.shopee_access_token = client.access_token
        doc.shopee_refresh_token = client.refresh_token
        doc.shopee_token_expiration_unix = int(time.time()) + client.timeout

        doc.shopee_shop_authorize_time = datetime.utcfromtimestamp(
            shop_profile["auth_time"],
        ).strftime("%Y-%m-%d %H:%M:%S")

        doc.shopee_shop_expire_time = datetime.utcfromtimestamp(
            shop_profile["expire_time"],
        ).strftime("%Y-%m-%d %H:%M:%S")

        doc.insert()
        frappe.db.commit()

    url = frappe.utils.get_url("app/branch")

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url


@frappe.whitelist()
def unauthorize():

    sign, unauth_url = client.auth_url("/api/v2/shop/cancel_auth_partner")
    unauth_url += f"&redirect={UNAUTHORIZE_REDIRECT_URL}"

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = unauth_url


@frappe.whitelist()
def unauthorize_callback():

    shop_id = int(frappe.request.args.getlist("shop_id")[0])

    shop_exists = frappe.db.exists(
        {
            "doctype": "Branch",
            "shopee_shop_id": shop_id,
        }
    )

    if shop_exists:

        branch_name = shop_exists[0][0]

        shop = frappe.get_doc(
            "Branch",
            branch_name,
        )

        shop.delete()
        frappe.db.commit()

    url = frappe.utils.get_url("app/branch")

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = url


@frappe.whitelist()
def get_authorize_url():

    url = client.shop_authorization(redirect_url=client.redirect_url)

    return url


@frappe.whitelist()
def get_unauthorize_url():

    sign, unauth_url = client.auth_url("/api/v2/shop/cancel_auth_partner")
    unauth_url += f"&redirect={UNAUTHORIZE_REDIRECT_URL}"

    return unauth_url
