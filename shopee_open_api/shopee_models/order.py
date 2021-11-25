from .base import ShopeeResponseBaseClass
from .payment_escrow import PaymentEscrow
from .order_item import OrderItem
from .product import Product
import frappe
from shopee_open_api.utils.datetime import datetime_string_from_unix


class Order(ShopeeResponseBaseClass):

    DOCTYPE = "Shopee Order"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_escrow = None
        self.order_items = [
            OrderItem(item, order_sn=self.get_order_sn(), shop_id=self.get_shop_id())
            for item in self.item_list
        ]

    def __str__(self):
        return f"{self.__class__.__name__}: {self.order_sn}"

    def make_primary_key(self):
        return self.order_sn

    def update_or_insert_with_items(self, ignore_permissions=False):

        self.update_or_insert(ignore_permissions=ignore_permissions)

        for order_item in self.order_items:
            order_item.update_or_insert(ignore_permissions=ignore_permissions)

        if frappe.db.get_single_value(
            "Shopee API Settings",
            "create_sales_order_after_shopee_order_has_been_created",
        ):
            self.create_sales_order(ignore_permissions=ignore_permissions)

        self.update_products_stock(ignore_permissions=ignore_permissions)

        return frappe.get_doc("Shopee Order", self.make_primary_key())

    def create_sales_order(self, ignore_permissions=False) -> None:
        """
        Create sales order from shopee order. It is called here instead of after_insert
        since creating a new sales order requires order items, which are created after the order has been created
        """
        order = frappe.get_doc(self.DOCTYPE, self.make_primary_key())

        try:
            order.create_sales_order(ignore_permissions=ignore_permissions)
        except frappe.exceptions.ValidationError as e:
            """
            This can happen due to shopee product not being matched with erpnext item
            or the order is already matched with a sales order
            """
            return

    def get_item_list_ids(self):
        return [item["item_id"] for item in self.item_list]

    def get_shopee_products(self):

        items = self.client.product.get_item_base_info(
            item_id_list=",".join(
                [str(item_id) for item_id in self.get_item_list_ids()]
            )
        )["response"]["item_list"]

        products = [Product(item, shop_id=self.get_shop_id()) for item in items]

        return products

    def update_products_stock(self, ignore_permissions=False):

        products = self.get_shopee_products()
        [product.update_or_insert(ignore_permissions) for product in products]

    def update_or_insert(self, ignore_permissions=False):

        if self.is_existing_in_database:
            order = frappe.get_doc(
                self.DOCTYPE,
                self.make_primary_key(),
            )
        else:
            order = frappe.get_doc(
                doctype=self.DOCTYPE,
                shopee_shop=self.get_shop_id(),
                order_sn=self.get_order_sn(),
            )

        order.order_status = self.get_order_status()
        order.total_amount = self.get_total_amount()
        order.currency = self.get_currency()
        order.region = self.get_region()
        order.cod = self.get_cod()
        order.checkout_shipping_carrier = self.get_checkout_shipping_carrier()
        order.buyer_cancel_reason = self.get_buyer_cancel_reason()
        order.cancel_reason = self.get_cancel_reason()
        order.credit_card_number = self.get_credit_card_number()
        order.days_to_ship = self.get_days_to_ship()
        order.message_to_seller = self.get_message_to_seller()
        order.note = self.get_note()
        order.payment_method = self.get_payment_method()
        order.shipping_carrier = self.get_shipping_carrier()
        order.split_up = self.get_split_up()
        order.pay_time = self.get_pay_time()
        order.pickup_done_time = self.get_pickup_done_time()
        order.update_time = self.get_update_time()
        order.ship_by_date = self.get_ship_by_date()
        order.create_time = self.get_create_time()
        order.estimated_shipping_fee = self.get_estimated_shipping_fee()
        order.actual_shipping_fee = self.get_actual_shipping_fee()
        order.shipping_fee_confirmed = self.get_shipping_fee_confirmed()
        order.reverse_shipping_fee = self.get_reverse_shipping_fee()
        order.buyer_user_id = self.get_buyer_user_id()
        order.buyer_username = self.get_buyer_username()
        order.buyer_cpf_id = self.get_buyer_cpf_id()
        order.recipient_name = self.get_recipient_name()
        order.recipient_full_address = self.get_recipient_full_address()
        order.recipient_city = self.get_recipient_city()
        order.recipient_district = self.get_recipient_district()
        order.recipient_phone = self.get_recipient_phone()
        order.recipient_region = self.get_recipient_region()
        order.recipient_state = self.get_recipient_state()
        order.recipient_town = self.get_recipient_town()
        order.recipient_zipcode = self.get_recipient_zipcode()

        ## details from payment escrow
        order.buyer_total_amount = self.get_order_income().get("buyer_total_amount")
        order.original_price = self.get_order_income().get("original_price")
        order.seller_discount = self.get_order_income().get("seller_discount")
        order.shopee_discount = self.get_order_income().get("shopee_discount")
        order.voucher_from_seller = self.get_order_income().get("voucher_from_seller")
        order.voucher_from_shopee = self.get_order_income().get("voucher_from_shopee")
        order.coins = self.get_order_income().get("coins")
        order.buyer_paid_shipping_fee = self.get_order_income().get(
            "buyer_paid_shipping_fee"
        )
        order.buyer_transaction_fee = self.get_order_income().get(
            "buyer_transaction_fee"
        )

        order.cross_border_tax = self.get_order_income().get("cross_border_tax")
        order.payment_promotion = self.get_order_income().get("payment_promotion")
        order.commission_fee = self.get_order_income().get("commission_fee")
        order.service_fee = self.get_order_income().get("service_fee")
        order.seller_transaction_fee = self.get_order_income().get(
            "seller_transaction_fee"
        )
        order.seller_lost_compensation = self.get_order_income().get(
            "seller_lost_compensation"
        )
        order.seller_coin_cash_back = self.get_order_income().get(
            "seller_coin_cash_back"
        )
        order.escrow_tax = self.get_order_income().get("escrow_tax")
        order.final_shipping_fee = self.get_order_income().get("final_shipping_fee")
        order.escrow_actual_shipping_fee = self.get_order_income().get(
            "actual_shipping_fee"
        )
        order.escrow_estimated_shipping_fee = self.get_order_income().get(
            "estimated_shipping_fee"
        )
        order.shopee_shipping_rebate = self.get_order_income().get(
            "shopee_shipping_rebate"
        )
        order.shipping_fee_discount_from_3pl = self.get_order_income().get(
            "shipping_fee_discount_from_3pl"
        )
        order.seller_shipping_discount = self.get_order_income().get(
            "seller_shipping_discount"
        )
        order.drc_adjustable_refund = self.get_order_income().get(
            "drc_adjustable_refund"
        )
        order.cost_of_goods_sold = self.get_order_income().get("cost_of_goods_sold")
        order.original_cost_of_goods_sold = self.get_order_income().get(
            "original_cost_of_goods_sold"
        )
        order.original_shopee_discount = self.get_order_income().get(
            "original_shopee_discount"
        )
        order.seller_return_refund = self.get_order_income().get("seller_return_refund")
        order.escrow_amount = self.get_order_income().get("escrow_amount")

        order.save(ignore_permissions=ignore_permissions)

        return order

    @property
    def is_existing_in_database(self):
        return frappe.db.exists(
            self.DOCTYPE,
            self.make_primary_key(),
        )

    def get_shop_id(self):
        return str(self.shop_id)

    def get_order_status(self):
        return self.order_status

    def get_order_sn(self):
        return self.order_sn

    def get_total_amount(self):
        return float(self.total_amount)

    def get_currency(self):
        return self.currency

    def get_region(self):
        return self.region

    def get_cod(self):
        return self.cod

    def get_checkout_shipping_carrier(self):
        return self.checkout_shipping_carrier

    def get_buyer_cancel_reason(self):
        return self.buyer_cancel_reason

    def get_cancel_reason(self):
        return self.cancel_reason

    def get_credit_card_number(self):
        return self.credit_card_number

    def get_days_to_ship(self):
        return self.days_to_ship

    def get_message_to_seller(self):
        return self.message_to_seller

    def get_note(self):
        return self.note

    def get_payment_method(self):
        return self.payment_method

    def get_shipping_carrier(self):
        return self.shipping_carrier

    def get_split_up(self):
        return self.split_up

    def get_pay_time(self):
        if self.pay_time:
            return datetime_string_from_unix(self.pay_time)
        return None

    def get_pickup_done_time(self):
        """Shopee returns 0 when the shipment hasn't been picked up yet instead of null"""

        if not self.pickup_done_time:
            return None
        return datetime_string_from_unix(self.pickup_done_time)

    def get_update_time(self):
        return datetime_string_from_unix(self.update_time)

    def get_ship_by_date(self):
        """Shopee returns 0 when the order status is UNPAID"""
        if not self.ship_by_date:
            return None
        return datetime_string_from_unix(self.ship_by_date)

    def get_create_time(self):
        return datetime_string_from_unix(self.create_time)

    def get_estimated_shipping_fee(self):
        return float(self.estimated_shipping_fee)

    def get_actual_shipping_fee(self):
        return float(self.actual_shipping_fee)

    def get_shipping_fee_confirmed(self):
        return self.actual_shipping_fee_confirmed

    def get_reverse_shipping_fee(self):
        return float(self.reverse_shipping_fee)

    def get_buyer_user_id(self):
        return str(self.buyer_user_id)

    def get_buyer_username(self):
        return self.buyer_username

    def get_buyer_cpf_id(self):
        return self.buyer_cpf_id

    def get_recipient_name(self):
        return self.recipient_address.get("name")

    def get_recipient_full_address(self):
        return self.recipient_address.get("full_address")

    def get_recipient_city(self):
        return self.recipient_address.get("city")

    def get_recipient_district(self):
        return self.recipient_address.get("district")

    def get_recipient_phone(self):
        return self.recipient_address.get("phone")

    def get_recipient_region(self):
        return self.recipient_address.get("region")

    def get_recipient_state(self):
        return self.recipient_address.get("state")

    def get_recipient_town(self):
        return self.recipient_address.get("town")

    def get_recipient_zipcode(self):
        return self.recipient_address.get("zipcode")

    def get_payment_escrow(self):

        if self.payment_escrow is None:
            escrow_response = self.client.payment.get_escrow_detail(
                order_sn=self.get_order_sn()
            )["response"]

            self.payment_escrow = PaymentEscrow(escrow_response)

        return self.payment_escrow

    def get_order_income(self):
        return self.get_payment_escrow().order_income
