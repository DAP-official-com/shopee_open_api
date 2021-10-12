from shopee_open_api.python_shopee import pyshopee2
from shopee_open_api.utils.client import get_client_from_branch
import frappe


PARTNER_ID = frappe.db.get_single_value("Shopee API Settings", "partner_id")
PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")

AUTHORIZE_REDIRECT_URL = (
    f"{frappe.utils.get_url()}/api/method/shopee_open_api.auth.authorize_callback"
)


def update_profile(branch, _):

    """
    Call shopee shop.update_profile when the branch is saved to the database.
    """

    if not frappe.db.exists("Branch", branch.name):
        return

    if not branch.shopee_shop_id:
        return

    client = get_client_from_branch(branch)

    client.shop.update_profile(
        shop_name=branch.name,
        shop_logo=branch.shopee_shop_logo,
        description=branch.shopee_shop_description,
    )
