import frappe
from shopee_open_api.exceptions import BadRequestError
from shopee_open_api.utils.client import get_client_from_shop_id
from shopee_open_api.shopee_models.product import Product
from shopee_open_api.scheduled_tasks.tasks import resync_products
from frappe import enqueue


@frappe.whitelist()
def reload_product_details_from_shopee(product_primary_key):

    product = frappe.get_doc("Shopee Product", product_primary_key)
    client = get_client_from_shop_id(product.shopee_shop)

    shopee_response = client.product.get_item_base_info(
        item_id_list=product.shopee_product_id
    )

    if shopee_response.get("error"):
        raise BadRequestError(
            f"{shopee_response.get('error')} {shopee_response.get('message')}"
        )

    product_details = shopee_response["response"]["item_list"][0]
    product = Product(product_details, shop_id=product.shopee_shop)
    product.update_or_insert()

    return {"message": "ok"}


@frappe.whitelist()
def create_new_item_and_add_to_product(product_primary_key):

    product = frappe.get_doc("Shopee Product", product_primary_key)
    product.create_new_item_and_add_to_product()

    return {"message": "ok"}


@frappe.whitelist()
def sync_products():
    enqueue("shopee_open_api.scheduled_tasks.product_tasks.sync_all_products")
    return
