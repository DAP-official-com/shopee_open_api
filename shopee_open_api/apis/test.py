import frappe
from shopee_open_api.utils.client import get_client_from_branch, get_client_from_shop
from tqdm import tqdm

import os, json


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
                "shopee_category_id": str(category["category_id"]),
            }
        ):
            continue

        new_category = {"doctype": "Shopee Product Category"}
        new_category["category"] = category["original_category_name"]
        new_category["category_id"] = category["category_id"]
        new_category["shopee_category_id"] = str(category["category_id"])
        new_category["is_group"] = category["has_children"]

        if category["parent_category_id"] != 0:
            new_category["parent_catagory_id"] = category["parent_category_id"]

        category = frappe.get_doc(new_category)
        category.insert()
        frappe.db.commit()

    categories_with_parent = frappe.db.get_list(
        "Shopee Product Category",
        filters={"parent_catagory_id": ("!=", "")},
        as_list=True,
        fields=[
            "name",
            "parent_catagory_id",
        ],
    )

    for category in categories_with_parent:
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

    shops = frappe.db.get_all("Shopee Shop")

    shop = frappe.get_doc("Shopee Shop", shops[0]["name"])

    client = get_client_from_shop(shop)

    orders = client.order.get_order_list(
        time_range_field="create_time",
        time_from=1634137703,
        time_to=1634638713,
        page_size=100,
        order_status="READY_TO_SHIP",
    )["response"]["order_list"]

    # to_ship_orders = client.order.get_shipment_list(page_size=100)

    # order_details = client.order.get_order_detail(
    #     order_sn_list=",".join([order["order_sn"] for order in orders]),
    #     response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf_id,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee",
    # )

    shipped_orders = client.logistics.ship_order(order_sn=orders[0]["order_sn"])

    return shipped_orders


@frappe.whitelist()
def test_client():

    branches = frappe.db.get_all("Branch")

    branch = frappe.get_doc("Branch", branches[0]["name"])

    client = get_client_from_branch(branch)

    return client.product.get_category()


def make_output_content(filename, response, note=None):

    output = {}
    output["content"] = response
    output["note"] = note

    content = json.dumps(output, indent=4, ensure_ascii=False).encode("utf-8").decode()

    with open(f"{filename}.json", "w") as output:
        output.write(content)


@frappe.whitelist()
def export_product_responses():

    branch_name = frappe.db.get_list("Branch")[0]["name"]

    branch = frappe.get_doc("Branch", branch_name)

    client = get_client_from_branch(branch)

    categories = client.product.get_category(language="TH")["response"]["category_list"]
    make_output_content("get_category", categories)

    item_upload_limit = client.product.get_item_limit()["response"]
    make_output_content(
        "get_item_limit", item_upload_limit, note="Used for validation?"
    )

    item_list = client.product.get_item_list(
        offset=0, page_size=100, item_status="NORMAL"
    )["response"]["item"]
    make_output_content(f"get_item_list item_status: NORMAL", item_list, note=None)

    item_ids = [str(item["item_id"]) for item in item_list]
    item_base_infos = client.product.get_item_base_info(
        item_id_list=",".join(item_ids),
        need_tax_info=True,
        need_complaint_policy=True,
    )["response"]["item_list"]
    make_output_content(
        f"get_item_base_info item_id_list: {item_ids}",
        item_base_infos,
        note="price_info and stock_info will not be returned if an item has variants",
    )

    for item in item_list:
        item_id = item["item_id"]
        item_model_list = client.product.get_model_list(item_id=item_id)["response"]
        make_output_content(
            f"get_model_list item_id_list: {item_id}",
            item_model_list,
            note="products with no varians will return empty object",
        )

    counter = 0
    for category in categories:
        category_id = category["category_id"]
        has_children = category["has_children"]
        category_name = category["original_category_name"]

        if has_children:
            continue

        counter += 1

        attributes = client.product.get_attributes(
            category_id=category_id, language="TH"
        )["response"]["attribute_list"]
        make_output_content(
            f"get_attributes category_name: {category_name} category_id: {category_id}",
            response=attributes,
            note="only categories without children are valid for input",
        )

        if counter == 2:
            break

    counter = 0
    for category in categories:

        category_id = category["category_id"]
        has_children = category["has_children"]
        category_name = category["original_category_name"]

        if has_children:
            continue

        counter += 1

        brands = client.product.get_brand_list(
            page_size=50,
            offset=0,
            category_id=category_id,
            status=1,  ## 1 normal, 2 pending branch
            language="TH",
        )["response"]["brand_list"]

        make_output_content(
            f"get_brand_list category_name: {category_name} category_id: {category_id}",
            response=brands,
            note="only categories without children are valid for input",
        )

        if counter == 2:
            break

    counter = 0
    for category in categories:

        category_id = category["category_id"]
        has_children = category["has_children"]
        category_name = category["original_category_name"]

        if has_children:
            continue
        #
        counter += 1
        dts_limit = client.product.get_dts_limit(
            category_id=category_id,
        )["response"]

        make_output_content(
            f"get_dts_limit category_name: {category_name} category_id: {category_id}",
            response=dts_limit,
            note="only categories without children are valid for input",
        )

        if counter == 2:
            break

    return


@frappe.whitelist()
def test_image_upload():

    branch_name = frappe.db.get_list("Branch")[0]["name"]

    branch = frappe.get_doc("Branch", branch_name)

    client = get_client_from_branch(branch)

    return client.mediaspace.upload_image("../whitecat.jpg")
