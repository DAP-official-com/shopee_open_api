import time
from frappe import enqueue
import frappe
from shopee_open_api.utils.client import get_client_from_shop


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

    response = client.product.get_item_list(
        offset=offset,
        item_status=item_status,
        page_size=100,
    )

    if response.get("error"):
        raise Exception(response.get("message"))

    product_list = response["response"]["item"]

    product_details = client.product.get_item_base_info(
        item_id_list=",".join([str(product["item_id"]) for product in product_list])
    )["response"]["item_list"]

    singular_products = [
        product for product in product_details if product.get("price_info")
    ]

    multi_variants_products = [
        product
        for product in product_details
        if product.get("price_info", False) == False
    ]

    for product in singular_products:
        shopee_product = frappe.get_doc(
            doctype="Shopee Product",
            shopee_product_id=str(product["item_id"]),
            shopee_model_id=str(0),
            item_status=product["item_status"],
            shopee_shop=shop.name,
            category=str(product["category_id"]),
            weight=float(product["weight"]),
            item_name=product["item_name"],
        )
        shopee_product.save()

    for product in multi_variants_products:

        model_details = client.product.get_model_list(item_id=product["item_id"])[
            "response"
        ]
        models = model_details["model"]
        variations = model_details["tier_variation"]

        variation_options = []

        for variation in variations:
            variation_options.append(
                [variation["option"] for variation in variation["option_list"]]
            )

        for model in models:
            variation_values = []
            for variation_index, option_index in enumerate(model["tier_index"]):
                variation_options[variation_index][option_index]
                variation_values.append(
                    variation_options[variation_index][option_index]
                )

            variant_name = "-".join(variation_values)

            shopee_product = frappe.get_doc(
                doctype="Shopee Product",
                shopee_product_id=str(product["item_id"]),
                shopee_model_id=str(model["model_id"]),
                item_status=product["item_status"],
                shopee_shop=shop.name,
                category=str(product["category_id"]),
                weight=float(product["weight"]),
                item_name=f"{product['item_name']} ({variant_name})",
            )
            shopee_product.save()

    has_next_page = response["response"].get("has_next_page")

    if has_next_page:
        start_pulling_products(
            shop_id=shop_id,
            offset=response["response"].get("next_offset"),
            item_status=item_status,
        )
    else:
        frappe.publish_realtime("msgprint", "All products downloaded")

    return True
