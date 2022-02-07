# Copyright (c) 2022, Dap Official and contributors
# For license information, please see license.txt

import frappe
import traceback

from erpnext.stock import stock_ledger
from frappe.model.document import Document
from shopee_open_api.exceptions import BadRequestError, OrderAutomationProcessingError
from shopee_open_api.python_shopee import pyshopee2
from shopee_open_api.shopee_open_api.doctype.shopee_shop import shopee_shop
from shopee_open_api.shopee_models import order
from shopee_open_api.utils import client as client_utils


class ShopeeOrderQueue(Document):
    def process_order(self):
        """Save order's details to the database and run order automation process."""
        order = self.get_order_detail()

        try:
            order.update_or_insert_with_items()
        except (OrderAutomationProcessingError, stock_ledger.NegativeStockError) as e:

            frappe.db.rollback()  ## Rollback any actions from the last committed automation step

            error_data = {
                "shop_id": self.shopee_shop,
                "code": 3,
                "data": {
                    "ordersn": self.order_sn,
                },
            }

            shopee_error = frappe.new_doc("Shopee Order Update Error")
            shopee_error.raw_data = str(error_data)
            shopee_error.error = str(traceback.format_exc())
            shopee_error.insert(ignore_permissions=True)
            frappe.db.commit()

        self.delete()
        frappe.db.commit()

    def get_order_detail(self) -> order.Order:
        """Call Shopee's API to retrieve the order latest details."""
        client = self.get_shop_client()
        order_detail_response = client.order.get_order_detail(
            order_sn_list=self.order_sn,
            response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf_id,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee",
        )

        if order_detail_response.get("error"):
            raise BadRequestError(
                f"{order_detail_response.get('error')} {order_detail_response.get('message')}"
            )

        order_details = order_detail_response["response"]["order_list"][0]

        order_object = order.Order(order_details, shop_id=self.shopee_shop)

        return order_object

    def get_shop_client(self) -> pyshopee2.Client:
        return client_utils.get_client_from_shop(self.get_shop_document())

    def get_shop_document(self) -> shopee_shop.ShopeeShop:
        return frappe.get_doc("Shopee Shop", self.shopee_shop)
