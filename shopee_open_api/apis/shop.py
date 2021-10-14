import frappe
import time
from shopee_open_api.utils.client import get_shopless_client, get_client_from_branch


@frappe.whitelist()
def reload_shop_details_from_shopee(branch_name):

    branch = frappe.get_doc("Branch", branch_name)
    client = get_client_from_branch(branch)

    shop_profile = client.shop.get_profile()["response"]
    shop_profile.update(client.shop.get_shop_info())

    branch.shopee_shop_name = shop_profile["shop_name"][:30]

    branch.shopee_shop_logo = shop_profile["shop_logo"]
    branch.shopee_shop_status = shop_profile["status"]
    branch.shopee_shop_description = shop_profile["description"]

    branch.save()

    frappe.db.commit()

    return {"message": "ok"}
