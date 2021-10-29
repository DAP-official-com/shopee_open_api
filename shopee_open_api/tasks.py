import time
from frappe import enqueue
import frappe
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.shopee_models.product import Product


def cron():
    return True


def start_pulling_products(**kwargs):
    enqueue("shopee_open_api.tasks.pull_products", **kwargs)


def pull_products(
    shop_id: str,
    offset: int = 0,
    item_status: str = "NORMAL",
    update_item_from=None,
):
    shop = frappe.get_doc("Shopee Shop", shop_id)
    client = get_client_from_shop(shop)

    if update_item_from:
        response = client.product.get_item_list(
            offset=offset,
            item_status=item_status,
            page_size=100,
            update_item_from=update_item_from,
        )
    else:
        response = client.product.get_item_list(
            offset=offset,
            item_status=item_status,
            page_size=100,
        )

    if response.get("error"):
        raise frappe.RetryBackgroundJobError(response.get("message"))

    product_list = response["response"]["item"]

    product_details = client.product.get_item_base_info(
        item_id_list=",".join([str(product["item_id"]) for product in product_list])
    )["response"]["item_list"]

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
            update_item_from=update_item_from,
        )
    else:
        frappe.publish_realtime("msgprint", "All products downloaded")

    return True
