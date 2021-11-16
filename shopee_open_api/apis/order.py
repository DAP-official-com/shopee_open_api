import frappe
from shopee_open_api.exceptions import BadRequestError
from shopee_open_api.utils.client import get_client_from_shop_id
from shopee_open_api.shopee_models.order import Order


@frappe.whitelist()
def reload_order_details_from_shopee(shop_id, order_sn):

    client = get_client_from_shop_id(shop_id)

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

    order.update_or_insert_with_items()

    frappe.db.commit()

    return {"message": "ok"}


@frappe.whitelist()
def create_sales_order_from_shopee_order(order_sn: str):
    order = frappe.get_doc("Shopee Order", order_sn)
    sales_order = order.create_sales_order()
    return sales_order
