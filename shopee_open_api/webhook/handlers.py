import frappe, json
from datetime import datetime
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.exceptions import BadRequestError


def handle_order_status_update(data: dict):

    shop_id = data.get("shop_id")

    order_sn = data.get("data").get("ordersn")

    shop = frappe.get_doc("Shopee Shop", str(shop_id))
    client = get_client_from_shop(shop)

    order_detail_response = client.order.get_order_detail(
        order_sn_list=order_sn,
        response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf_id,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee",
    )

    if order_detail_response.get("error"):
        raise BadRequestError(
            f"{order_detail_response.get('error')} {order_detail_response.get('message')}"
        )

    order_details = order_detail_response["response"]["order_list"][0]

    if frappe.db.exists("Shopee Order", order_sn):
        order = frappe.get_doc("Shopee Order", order_sn)
    else:
        create_time = datetime.utcfromtimestamp(order_details["create_time"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        order = frappe.get_doc(
            doctype="Shopee Order",
            order_sn=order_sn,
            create_time=create_time,
            shopee_shop=str(shop_id),
        )

    order.order_status = order_details["order_status"]
    order.total_amount = float(order_details.get("total_amount"))
    order.currency = order_details["currency"]
    order.region = order_details["region"]
    order.cod = order_details["cod"]
    order.checkout_shipping_carrier = order_details["checkout_shipping_carrier"]
    order.buyer_cancel_reason = order_details["buyer_cancel_reason"]
    order.credit_card_number = order_details["credit_card_number"]
    order.days_to_ship = order_details["days_to_ship"]
    order.message_to_seller = order_details["message_to_seller"]
    order.note = order_details["note"]
    order.payment_method = order_details["payment_method"]
    order.shipping_carrier = order_details["shipping_carrier"]
    order.split_up = order_details["split_up"]

    if order_details["pay_time"]:
        order.pay_time = datetime.utcfromtimestamp(order_details["pay_time"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    if order_details["pickup_done_time"]:
        order.pay_time = datetime.utcfromtimestamp(
            order_details["pickup_done_time"]
        ).strftime("%Y-%m-%d %H:%M:%S")

    order.update_time = datetime.utcfromtimestamp(
        order_details["update_time"]
    ).strftime("%Y-%m-%d %H:%M:%S")

    order.ship_by_date = datetime.utcfromtimestamp(
        order_details["ship_by_date"]
    ).strftime("%Y-%m-%d %H:%M:%S")

    order.save(ignore_permissions=True)

    frappe.db.commit()
