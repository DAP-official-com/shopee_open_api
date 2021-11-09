import frappe
from shopee_open_api.utils.client import (
    get_client_from_shop,
    get_client_from_shop_id,
)
from tqdm import tqdm
from shopee_open_api.shopee_models.product import Product
from shopee_open_api.shopee_models.order import Order
import uuid

@frappe.whitelist()
def get_products():
    shops = frappe.db.get_all("Shopee Shop")
    shop_id = shops[0].name

    client = get_client_from_shop_id(shop_id)

    products = []

    for offset in range(0, 150, 50):
        products += client.product.get_item_list_and_info(
            offset=offset, page_size=50, item_status="NORMAL"
        )["response"]["item_list"]

    return products


@frappe.whitelist()
def test_apis():

    shops = frappe.db.get_all("Shopee Shop")
    shop_id = shops[0].name

    client = get_client_from_shop_id(shop_id)

    product_apis = [
        attr for attr in client.payment.__dir__() if not attr.startswith("__")
    ]

    for api in product_apis:
        if callable(getattr(client.payment, api)):
            try:
                r = getattr(client.payment, api)()
                if r.get("error"):
                    print(f"{api} {r.get('message')}")
                else:
                    print(f"{api} is working")
            except Exception as e:
                print(api, "cannot be called")

    return product_apis


@frappe.whitelist()
def test_get_payout_detail():

    shops = frappe.db.get_all("Shopee Shop")
    shop_id = shops[0].name

    client = get_client_from_shop_id(shop_id)

    order_detail_response = client.order.get_order_detail(
        order_sn_list="210701RR6EPHR7",
        response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason",
    )

    order = Order(
        order_detail_response["response"]["order_list"][0],
        shop_id=shop_id,
    )

    return order.get_payment_escrow().to_json()


@frappe.whitelist()
def test_order_detail():

    shops = frappe.db.get_all("Shopee Shop")
    shop_id = shops[0].name

    client = get_client_from_shop_id(shop_id)

    r = client.order.get_order_detail(
        order_sn_list="2110307WJJED6R",
        response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf_id,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee",
    )

    return r


@frappe.whitelist()
def test_tracking_info():

    shops = frappe.db.get_all("Shopee Shop")
    shop_id = shops[0].name

    client = get_client_from_shop_id(shop_id)

    r = client.logistics.get_tracking_info(
        order_sn="211102GC0R9731",
    )

    return r


@frappe.whitelist()
def test_get_shopee_products():

    shops = frappe.db.get_all("Shopee Shop")
    shop_id = shops[0].name

    client = get_client_from_shop_id(shop_id)

    product_details = client.product.get_item_list_and_info(
        offset=0, page_size=100, item_status="NORMAL"
    )["response"]["item_list"]

    products = [
        Product(product_detail, shop_id=shop_id) for product_detail in product_details
    ]

    singular_products = [product for product in products if not product.has_model]

    [product.update_or_insert() for product in singular_products]

    multi_variants_products = [product for product in products if product.has_model]

    [product.update_or_insert() for product in multi_variants_products]

    frappe.db.commit()


@frappe.whitelist()
def get_category_list():

    shops = frappe.db.get_all("Shopee Shop")

    shop = frappe.get_doc("Shopee Shop", shops[0]["name"])

    client = get_client_from_shop(shop)

    categories = client.product.get_category()["response"]["category_list"]

    for category in tqdm(categories):

        if frappe.db.exists(
            {
                "doctype": "Shopee Product Category",
                "category_id": str(category["category_id"]),
            }
        ):
            continue

        new_category = {"doctype": "Shopee Product Category"}
        new_category["category"] = category["original_category_name"]
        new_category["category_id"] = str(category["category_id"])
        new_category["is_group"] = category["has_children"]

        if category["parent_category_id"] != 0:
            new_category["parent_category_id"] = category["parent_category_id"]

        category = frappe.get_doc(new_category)
        category.insert()
        frappe.db.commit()

    categories_with_parent = frappe.db.get_list(
        "Shopee Product Category",
        filters={"parent_category_id": ("!=", "")},
        as_list=True,
        fields=[
            "name",
            "parent_category_id",
        ],
    )

    for category in tqdm(categories_with_parent):
        parent_category_name = frappe.db.get_list(
            "Shopee Product Category",
            filters={"category_id": category[1]},
            fields=[
                "name",
            ],
            as_list=True,
        )[0][0]
        frappe.db.set_value(
            "Shopee Product Category",
            category[0],
            "parent_shopee_product_category",
            parent_category_name,
        )
        frappe.db.commit()

    return categories_with_parent


@frappe.whitelist()
def test_add_product():

    shops = frappe.db.get_all("Shopee Shop")

    shop = frappe.get_doc("Shopee Shop", shops[0]["name"])

    client = get_client_from_shop(shop)

    original_price = 1000
    description = "This is just a nice description for a product"
    item_name = "Hottest item rn"
    normal_stock = 20

    image_response = client.mediaspace.upload_image(
        image="./mysite.localhost/public/files/download_new.png"
    )
    image_id = image_response["response"]["image_info"]["image_id"]

    image = {}
    image["image_id_list"] = [
        image_id,
    ]

    category_response = client.product.get_category()

    node_category = [
        category
        for category in category_response["response"]["category_list"]
        if category["has_children"] == False
    ][0]

    brand_response = client.product.get_brand_list(
        offset=0, page_size=100, category_id=node_category["category_id"], status=1
    )

    selected_brand = brand_response["response"]["brand_list"][1]

    dts_limit = client.product.get_dts_limit(category_id=node_category["category_id"])

    attributes = client.product.get_attributes(category_id=node_category["category_id"])
    required_attributes = [
        attribute
        for attribute in attributes["response"]["attribute_list"]
        if attribute["is_mandatory"]
    ]

    attribute_list = []
    attribute_info = {}
    attribute_list.append(attribute_info)

    attribute_info["attribute_id"] = required_attributes[0]["attribute_id"]
    attribute_list[0]["attribute_value_list"] = []

    attribute_values = {}
    attribute_values["value_id"] = 0
    attribute_values["original_value_name"] = "FDA Regis No. 0000001"

    attribute_list[0]["attribute_value_list"].append(attribute_values)

    channel_list = client.logistics.get_channel_list()["response"][
        "logistics_channel_list"
    ]

    logistic_list = []
    logistic_info = {}
    logistic_info["logistic_id"] = channel_list[0]["logistics_channel_id"]
    logistic_info["enabled"] = channel_list[0]["enabled"]
    logistic_list.append(logistic_info)

    support_size_chart = client.product.support_size_chart(
        category_id=node_category["category_id"]
    )

    added_item = client.product.add_item(
        original_price=original_price,
        description=description,
        item_name=item_name,
        normal_stock=normal_stock,
        logistic_info=logistic_list,
        attribute_list=attribute_list,
        category_id=node_category["category_id"],
        image=image,
        brand=selected_brand,
        weight=1,
    )

    return added_item


@frappe.whitelist()
def test_get_orders():

    shop = frappe.get_last_doc("Shopee Shop")

    client = get_client_from_shop(shop)

    orders = client.order.get_order_list(
        time_range_field="create_time",
        time_from=1634137703,
        time_to=1634807647,
        page_size=100,
        order_status="CANCELLED",
    )["response"]["order_list"]

    # to_ship_orders = client.order.get_shipment_list(page_size=100)

    order_details = client.order.get_order_detail(
        order_sn_list=",".join([order["order_sn"] for order in orders]),
        response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf_id,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee",
    )

    # shipped_orders = client.logistics.ship_order(order_sn=orders[0]["order_sn"])

    return order_details
