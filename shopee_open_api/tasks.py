import time
from frappe import enqueue
import frappe
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.shopee_models.product import Product
from shopee_open_api.scheduled_tasks.tasks import update_products


def cron():
    update_products()
