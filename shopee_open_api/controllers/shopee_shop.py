from shopee_open_api.utils.client import get_client_from_branch, get_client_from_shop
import frappe


PARTNER_ID = frappe.db.get_single_value("Shopee API Settings", "partner_id")
PARTNER_KEY = frappe.db.get_single_value("Shopee API Settings", "partner_key")

AUTHORIZE_REDIRECT_URL = (
    f"{frappe.utils.get_url()}/api/method/shopee_open_api.auth.authorize_callback"
)


def update_profile(shopee_shop, _):

    """
    Call shopee shop.update_profile when the shop is saved to the database.
    """

    client = get_client_from_shop(shopee_shop)

    updated_fields = {
        "shop_name": shopee_shop.shop_name,
        "description": shopee_shop.description,
    }

    version_before_save = shopee_shop.get_doc_before_save()

    if version_before_save:
        old_logo_url = version_before_save.logo
        new_logo_url = shopee_shop.logo

        if old_logo_url != new_logo_url:
            updated_fields["shop_logo"] = shopee_shop.shopee_shop_logo

    r = client.shop.update_profile(**updated_fields)

    if r.get("error"):
        frappe.throw(f'Shopee values update failed: {r.get("message")}')


def retrieve_all_products(branch, event_type):
    pass

    # client = get_client_from_branch(branch)

    # r = client.product.get_item_list(offset=0, page_size=100, item_status="NORMAL")

    # print(r)
