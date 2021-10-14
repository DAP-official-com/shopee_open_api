import time
from shopee_open_api.python_shopee.pyshopee2 import Client
from erpnext.hr.doctype.branch.branch import Branch
import frappe

PARTNER_ID = frappe.db.get_single_value("Shopee API Settings", "partner_id")
PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")
TEST_MODE = frappe.db.get_single_value("Shopee API Settings", "live_mode") == 0


AUTHORIZE_REDIRECT_URL = (
    f"{frappe.utils.get_url()}/api/method/shopee_open_api.auth.authorize_callback"
)


def get_shopless_client() -> Client:

    client = Client(
        shop_id=0,
        partner_id=PARTNER_ID,
        partner_key=PARTNER_KEY,
        redirect_url=AUTHORIZE_REDIRECT_URL,
        test_env=TEST_MODE,
    )

    return client


def get_client_from_branch(branch: Branch) -> Client:

    client = get_shopless_client()
    client.shop_id = int(branch.shopee_shop_id)
    client.access_token = branch.shopee_access_token
    client.refresh_token = branch.shopee_refresh_token
    client.expiration_unix = branch.shopee_token_expiration_unix

    if client.is_token_almost_expired:

        client.refresh_current_token()

        frappe.db.set_value(
            "Branch",
            branch.name,
            {
                "shopee_access_token": client.access_token,
                "shopee_refresh_token": client.refresh_token,
                "shopee_token_expiration_unix": client.expiration_unix,
            },
            update_modified=False,
        )

        frappe.db.commit()

    return client
