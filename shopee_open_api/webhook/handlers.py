import frappe, json
import traceback

from erpnext.stock import stock_ledger
from datetime import datetime
from shopee_open_api import utils
from shopee_open_api.exceptions import BadRequestError, OrderAutomationProcessingError
from shopee_open_api.shopee_models.order import Order


def handle_order_status_update(data: dict):

    shop_id = data.get("shop_id")

    order_sn = data.get("data").get("ordersn")

    shop = frappe.get_doc("Shopee Shop", str(shop_id))
    client = utils.client.get_client_from_shop(shop)

    order_detail_response = client.order.get_order_detail(
        order_sn_list=order_sn,
        response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf_id,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee",
    )

    if order_detail_response.get("error"):
        raise BadRequestError(
            f"{order_detail_response.get('error')} {order_detail_response.get('message')}"
        )

    order_details = order_detail_response["response"]["order_list"][0]

    order = Order(order_details, shop_id=shop_id)

    if order.is_before_ignore_date:
        return

    if shop.hold_order:

        if frappe.db.exists(
            {
                "doctype": "Shopee Order Queue",
                "shopee_shop": shop.name,
                "order_sn": order_sn,
            }
        ):
            return

        new_order_queue = frappe.new_doc("Shopee Order Queue")
        new_order_queue.shopee_shop = shop.name
        new_order_queue.order_sn = order_sn
        new_order_queue.insert()

        return

    try:
        order.update_or_insert_with_items()
    except (OrderAutomationProcessingError, stock_ledger.NegativeStockError) as e:

        frappe.db.rollback()  ## Rollback any actions from the last committed automation step

        shopee_error = frappe.new_doc("Shopee Order Update Error")
        shopee_error.raw_data = str(data)
        shopee_error.error = str(traceback.format_exc())
        shopee_error.insert(ignore_permissions=True)
        frappe.db.commit()

        pass
