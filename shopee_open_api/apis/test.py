import frappe
from shopee_open_api.utils.client import get_client_from_branch


import os, json


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
