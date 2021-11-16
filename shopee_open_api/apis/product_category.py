import frappe
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.exceptions import NoShopAuthorizedError


@frappe.whitelist()
def import_categories():

    shops = frappe.db.get_all("Shopee Shop", filters={"authorized": True})

    if len(shops) == 0:
        frappe.throw("At least one shop must be authorized", exc=NoShopAuthorizedError)

    shop = frappe.get_doc("Shopee Shop", shops[0]["name"])

    client = get_client_from_shop(shop)

    categories = client.product.get_category()["response"]["category_list"]

    for category in categories:

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

    return {"success": True}
