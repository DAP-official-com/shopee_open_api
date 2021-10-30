import time
from frappe import enqueue
import frappe
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.shopee_models.product import Product


# def update_products():
#     return True
#     frappe.publish_realtime("msgprint", "All products downloaded")


def start_pulling_products(**kwargs):
    enqueue("shopee_open_api.tasks.product_tasks.pull_products", **kwargs)
