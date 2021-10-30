import frappe
import time
from datetime import datetime
from shopee_open_api.utils.client import get_shopless_client
from shopee_open_api.tasks.tasks import start_pulling_products

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
    shop_id = frappe.request.args.getlist("shop_id")[0]

    client.code = code
    client.shop_id = shop_id
    client.get_token()

    shop_profile = client.shop.get_profile()["response"]
    shop_profile.update(client.shop.get_shop_info())

    shop_exists = frappe.db.exists({"doctype": "Shopee Shop", "shop_id": shop_id})

    if shop_exists:
        shop = frappe.get_doc("Shopee Shop", shop_id)
    else:
        shop = frappe.new_doc("Shopee Shop")
        shop.shop_id = shop_id
        shop.token = shop_id

    shop.shop_name = shop_profile["shop_name"][:30]
    shop.logo = shop_profile["shop_logo"]
    shop.status = shop_profile["status"]
    shop.description = shop_profile["description"]
    shop.authorized = True

    if shop_exists:
        token = frappe.get_doc("Shopee Token", shop_id)
    else:
        token = frappe.new_doc("Shopee Token")
        token.shop_id = shop_id

    token.access_token = client.access_token
    token.refresh_token = client.refresh_token
    token.token_expiration_unix = int(time.time()) + client.timeout

    token.authorization_time = datetime.utcfromtimestamp(
        shop_profile["auth_time"],
    ).strftime("%Y-%m-%d %H:%M:%S")

    token.expiration_time = datetime.utcfromtimestamp(
        shop_profile["expire_time"],
    ).strftime("%Y-%m-%d %H:%M:%S")

    token.save()
    shop.save()

    branch_exists = frappe.db.exists(
        {
            "doctype": "Branch",
            "shopee_shop": shop_id,
        }
    )

    if branch_exists:
        branch = frappe.get_doc("Branch", branch_exists[0][0])
    else:
        branch = frappe.new_doc("Branch")
        branch.shopee_shop = shop_id

    branch.branch = f"Shopee {shop_profile['shop_name']}"

    branch.save()

    frappe.db.commit()

    start_pulling_products(shop_id=shop_id)

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

    shop_id = frappe.request.args.getlist("shop_id")[0]

    shop_exists = frappe.db.exists("Shopee Shop", shop_id)

    if shop_exists:

        shop = frappe.get_doc(
            "Shopee Shop",
            shop_id,
        )
        shop.authorized = False
        shop.save()

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
