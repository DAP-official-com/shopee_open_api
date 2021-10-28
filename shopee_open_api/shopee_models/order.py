from .base import ShopeeResponseBaseClass
from .order_item import OrderItem
import frappe
from shopee_open_api.utils.datetime import datetime_string_from_unix


class Order(ShopeeResponseBaseClass):

    DOCTYPE = "Shopee Order"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = [
            OrderItem(item, order_sn=self.get_order_sn(), shop_id=self.get_shop_id())
            for item in self.item_list
        ]

    def __str__(self):
        return f"{self.__class__.__name__}: {self.order_sn}"

    def make_primary_key(self):
        return self.order_sn

    def update_or_insert_with_items(self, ignore_permissions=False):

        self.update_or_insert(ignore_permissions=ignore_permissions)

        for item in self.items:
            item.update_or_insert(ignore_permissions=ignore_permissions)

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

        order.save(ignore_permissions=ignore_permissions)

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
