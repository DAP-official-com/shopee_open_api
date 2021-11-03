import frappe
from shopee_open_api.exceptions import BadRequestError
from shopee_open_api.utils.client import get_client_from_shop_id
from shopee_open_api.shopee_models.product import Product


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
