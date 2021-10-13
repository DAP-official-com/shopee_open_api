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

    old_logo_url = branch.get_doc_before_save().shopee_shop_logo
    new_logo_url = branch.shopee_shop_logo

    updated_fields = {
        "shop_name": branch.name,
        "shop_logo": branch.shopee_shop_logo,
        "description": branch.shopee_shop_description,
    }

    if old_logo_url == new_logo_url:
        updated_fields.pop("shop_logo", None)

    r = client.shop.update_profile(**updated_fields)

    if r.get("error"):
        frappe.throw(f'Shopee values update failed: {r.get("message")}')
