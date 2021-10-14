import time
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

    ## Need latest branch in database as an argument for get_client_from_branch
    ## As sometimes the branch in the form does not have the latest access token
    branch_in_db = frappe.get_doc("Branch", branch.name)
    client = get_client_from_branch(branch_in_db)

    ## Manually manipuate the token values in the branch being saved
    ## As sometimes the branch in the form does not have the latest access token
    branch.shopee_access_token = client.access_token
    branch.shopee_refresh_token = client.refresh_token
    branch.shopee_token_expiration_unix = client.expiration_unix

    updated_fields = {
        "shop_name": branch.shopee_shop_name,
        "description": branch.shopee_shop_description,
    }

    version_before_save = branch.get_doc_before_save()

    if version_before_save:
        old_logo_url = version_before_save.shopee_shop_logo
        new_logo_url = branch.shopee_shop_logo

        if old_logo_url != new_logo_url:
            updated_fields["shop_logo"] = branch.shopee_shop_logo

    r = client.shop.update_profile(**updated_fields)

    if r.get("error"):
        frappe.throw(f'Shopee values update failed: {r.get("message")}')


def retrieve_all_products(branch, event_type):

    client = get_client_from_branch(branch)

    r = client.product.get_item_list(offset=0, page_size=100, item_status="NORMAL")

    print(r)
