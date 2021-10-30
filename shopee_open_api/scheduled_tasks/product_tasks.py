import frappe
import time
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.shopee_models.product import Product
from .tasks import start_pulling_products


def pull_products(
    shop_id: str,
    offset: int = 0,
    item_status: str = "NORMAL",
    update_time_from=None,
    notify_user=False,
):
    shop = frappe.get_doc("Shopee Shop", shop_id)
    client = get_client_from_shop(shop)

    if update_time_from:
        response = client.product.get_item_list(
            offset=offset,
            item_status=item_status,
            page_size=50,
            update_time_from=update_time_from,
        )
    else:
        response = client.product.get_item_list(
            offset=offset,
            item_status=item_status,
            page_size=50,
        )

    if response.get("error"):

        frappe.publish_realtime(
            "msgprint", response.get("message")
        ) if notify_user else None

        raise frappe.RetryBackgroundJobError(response.get("message"))

    if response.get("response", {}).get("total_count", 0) == 0:

        frappe.publish_realtime(
            "msgprint", "All products downloaded"
        ) if notify_user else None

        return

    product_list = response["response"]["item"]

    product_details_response = client.product.get_item_base_info(
        item_id_list=",".join([str(product["item_id"]) for product in product_list])
    )

    product_details = product_details_response["response"]["item_list"]

    if product_details_response.get("error"):

        frappe.publish_realtime(
            "msgprint", product_details_response.get("message")
        ) if notify_user else None

        raise frappe.RetryBackgroundJobError(response.get("message"))

    products = [
        Product(product_detail, shop_id=shop.name) for product_detail in product_details
    ]

    singular_products = [product for product in products if not product.has_model]

    [product.update_or_insert() for product in singular_products]

    multi_variants_products = [product for product in products if product.has_model]

    [product.update_or_insert() for product in multi_variants_products]

    has_next_page = response["response"].get("has_next_page")

    if has_next_page:
        start_pulling_products(
            shop_id=shop_id,
            offset=response["response"].get("next_offset"),
            item_status=item_status,
            update_time_from=update_time_from,
        )
    else:
        frappe.publish_realtime(
            "msgprint", "All products downloaded"
        ) if notify_user else None

    return True


def update_products():

    shops = frappe.db.get_all(
        "Shopee Shop",
        filters={"authorized": True},
        fields=["shop_id", "last_product_update"],
    )

    for shop in shops:

        if shop.last_product_update == 0:
            start_pulling_products(
                shop_id=shop["shop_id"],
                offset=0,
                item_status="NORMAL",
            )
        else:
            start_pulling_products(
                shop_id=shop["shop_id"],
                offset=0,
                item_status="NORMAL",
                update_time_from=shop["last_product_update"] - 60,
            )

    frappe.db.set_value(
        "Shopee Shop",
        shop["shop_id"],
        {
            "last_product_update": int(time.time()),
        },
    )
