from frappe import enqueue
import frappe
from shopee_open_api.shopee_open_api.doctype.shopee_wallet_transaction.shopee_wallet_transaction import (
    ShopeeWalletTransaction,
)


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


def update_wallet_transactions():

    shops = [
        frappe.get_doc("Shopee Shop", name)
        for name in frappe.get_all("Shopee Shop", pluck="name")
    ]

    for shop in shops:
        shop.update_wallet_transactions()


def process_withdrawal_transactions():

    transactions_to_process = ShopeeWalletTransaction.pending_withdrawals_to_process()
    for transaction in transactions_to_process:
        transaction.process_payment()
