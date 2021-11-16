import time
from shopee_open_api.python_shopee.pyshopee2 import Client
from erpnext.hr.doctype.branch.branch import Branch
from shopee_open_api.exceptions import NotShopeeBranchError, NotAuthorizedError
from shopee_open_api.shopee_open_api.doctype.shopee_shop.shopee_shop import ShopeeShop
import frappe


def get_shopless_client() -> Client:

    PARTNER_ID = frappe.db.get_single_value("Shopee API Settings", "partner_id")
    PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")
    TEST_MODE = frappe.db.get_single_value("Shopee API Settings", "live_mode") == 0
    ONLY_GET_ALLOWED = (
        frappe.db.get_single_value(
            "Shopee API Settings", "prevent_making_changes_on_shopee_portal"
        )
        == 1
    )
    AUTHORIZE_REDIRECT_URL = (
        f"{frappe.utils.get_url()}/api/method/shopee_open_api.auth.authorize_callback"
    )

    client = Client(
        shop_id=0,
        partner_id=PARTNER_ID,
        partner_key=PARTNER_KEY,
        redirect_url=AUTHORIZE_REDIRECT_URL,
        test_env=TEST_MODE,
        only_get_allowed=ONLY_GET_ALLOWED,
    )

    return client


def get_client_from_branch(branch: Branch) -> Client:

    if not branch.shopee_shop:
        raise NotShopeeBranchError(f"The branch {branch.name} is not a Shopee's shop")

    shop = frappe.get_doc("Shopee Shop", branch.shopee_shop)

    if not shop.authorized:
        raise NotAuthorizedError("This shop has been unauthorized")

    token = frappe.get_doc("Shopee Token", branch.shopee_shop)

    client = get_shopless_client()
    client.shop_id = int(branch.shopee_shop)
    client.access_token = token.access_token
    client.refresh_token = token.refresh_token
    client.expiration_unix = token.token_expiration_unix

    if client.is_token_almost_expired:

        client.refresh_current_token()

        frappe.db.set_value(
            "Shopee Token",
            branch.shopee_shop,
            {
                "access_token": client.access_token,
                "refresh_token": client.refresh_token,
                "token_expiration_unix": client.expiration_unix,
            },
        )

        frappe.db.commit()

    return client


def get_client_from_shop(shop: ShopeeShop) -> Client:

    if not shop.authorized:
        raise NotAuthorizedError("This shop has been unauthorized")

    token = frappe.get_doc("Shopee Token", shop.shop_id)

    client = get_shopless_client()
    client.shop_id = int(shop.shop_id)
    client.access_token = token.access_token
    client.refresh_token = token.refresh_token
    client.expiration_unix = token.token_expiration_unix

    if client.is_token_almost_expired:

        client.refresh_current_token()

        frappe.db.set_value(
            "Shopee Token",
            shop.shop_id,
            {
                "access_token": client.access_token,
                "refresh_token": client.refresh_token,
                "token_expiration_unix": client.expiration_unix,
            },
        )

        frappe.db.commit()

    return client


def get_client_from_shop_id(shop_id) -> Client:

    shop = frappe.get_doc("Shopee Shop", str(shop_id))
    return get_client_from_shop(shop)
