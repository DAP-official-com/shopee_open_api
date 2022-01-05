import frappe
from shopee_open_api.utils.client import (
    get_client_from_shop,
    get_client_from_shop_id,
)
import time, json
from tqdm import tqdm
from shopee_open_api.shopee_models.product import Product
from shopee_open_api.shopee_models.order import Order
from shopee_open_api.python_shopee.pyshopee2.exceptions import OnlyGetMethodAllowedError
import uuid
from shopee_open_api.python_shopee.pyshopee2.client import registered_module

ignored_apis = [
    "get_item_list_and_info",
    "upload_image",
]

ignored_modules = [
    "chat",
]


@frappe.whitelist()
def test_apis():

    shops = frappe.db.get_all("Shopee Shop")
    shop_id = shops[0].name

    client = get_client_from_shop_id(shop_id)

    file_object = open(f"python_shopee_api_testing_{time.time()}.txt", "a")

    for module in registered_module.keys():

        if module in ignored_modules:
            continue

        file_object.write(f"{module}'s methods tested \n")

        apis = [
            attr
            for attr in getattr(client, module).__dir__()
            if not attr.startswith("__")
        ]

        for api in apis:
            print(f"Testing {api}")

            if api in ignored_apis:
                continue

            if callable(getattr(getattr(client, module), api)):
                r, uri, method = getattr(getattr(client, module), api)()
                file_object.write(f"\t {api}: {r.status_code}: {method}: {uri}\n")

        time.sleep(0.5)
        file_object.write("\n\n")
