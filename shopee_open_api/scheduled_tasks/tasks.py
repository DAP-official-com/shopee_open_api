import time
from frappe import enqueue
import frappe
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.shopee_models.product import Product


def update_products():
    enqueue("shopee_open_api.scheduled_tasks.product_tasks.update_products")


def start_pulling_products(**kwargs):
    enqueue("shopee_open_api.scheduled_tasks.product_tasks.pull_products", **kwargs)


def process_order_queue():

    queue_items = [
        frappe.get_doc("Shopee Order Queue", name)
        for name in frappe.get_all("Shopee Order Queue", pluck="name")
    ]

    for queue_item in queue_items:

        if queue_item.get_shop_document().hold_order:
            continue

        queue_item.process_order()
