import frappe
from shopee_open_api.utils.client import get_client_from_shop


@frappe.whitelist()
def reload_shop_details_from_shopee(shop_id):

    shop = frappe.get_doc("Shopee Shop", shop_id)
    client = get_client_from_shop(shop)

    shop_profile = client.shop.get_profile()["response"]
    shop_profile.update(client.shop.get_shop_info())

    shop.shop_name = shop_profile["shop_name"][:30]

    shop.logo = shop_profile["shop_logo"]
    shop.status = shop_profile["status"]
    shop.description = shop_profile["description"]

    shop.save()

    frappe.db.commit()

    return {"message": "ok"}
