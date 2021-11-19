# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from shopee_open_api.shopee_models.customer import Customer
from shopee_open_api.shopee_models.address import Address
from shopee_open_api.shopee_open_api.doctype.shopee_order_item.shopee_order_item import (
    ShopeeOrderItem,
)
from typing import List


class ShopeeOrder(Document):
    def get_shopee_shop_instance(self):
        return frappe.get_doc("Shopee Shop", self.shopee_shop)

    @property
    def customer_detail(self) -> dict:

        customer = {}

        # data for Customer Doctype
        customer["customer_type"] = "Individual"
        customer["customer_group"] = "Individual"
        customer["customer_name"] = self.recipient_name
        customer["territory"] = frappe.db.get_default("Country")
        customer["username"] = self.buyer_username
        customer["user_id"] = self.buyer_user_id
        customer["shopee_user_id"] = self.buyer_user_id
        customer["mobile_no"] = self.recipient_phone

        return customer

    def get_customer_instance(self) -> Customer:
        """Get an instance of a customer (shopee customer, not erpnext customer)"""
        return Customer.from_shopee_customer(**self.customer_detail)

    @property
    def address_detail(self) -> dict:
        address = {}

        address["city"] = self.recipient_city
        address["country"] = frappe.db.get_default("Country")
        address["state"] = self.recipient_state
        address["phone"] = self.recipient_phone
        address["pincode"] = self.recipient_zipcode
        address["address_type"] = "Postal"
        address["full_address"] = self.recipient_full_address

        address["customer"] = self.get_customer_instance()

        return address

    def get_address_instance(self) -> Address:
        """Get an instance of an address (shopee address, not erpnext address)"""
        return Address.from_shopee_address(**self.address_detail)

    def create_sales_order(self, ignore_permissions=False):
        """Create Sales Order document from Shopee Order"""

        self.create_sales_order_validate()
        self.pre_create_sales_order(ignore_permissions=ignore_permissions)

        shop = self.get_shopee_shop_instance()

        new_sales_order = frappe.new_doc("Sales Order")
        new_sales_order.customer = self.get_customer_instance().get_primary_key()
        new_sales_order.order_type = "Sales"
        new_sales_order.transaction_date = self.create_time
        new_sales_order.delivery_date = self.create_time
        new_sales_order.customer_address = self.get_address_instance().get_primary_key()
        new_sales_order.set_warehouse = shop.get_warehouse().name

        for order_item in self.order_items:
            shopee_product = order_item.get_shopee_product()
            item = shopee_product.get_item()

            sales_order_item = new_sales_order.append("items", {})
            sales_order_item.item_code = item.name
            sales_order_item.qty = order_item.qty
            sales_order_item.rate = order_item.model_discounted_price

        new_sales_order.insert(ignore_permissions=ignore_permissions)

        self.sales_order = new_sales_order.name

        self.save(ignore_permissions=ignore_permissions)

        return new_sales_order

    @property
    def order_items(self) -> List[ShopeeOrderItem]:
        return self.get("shopee_order_items")

    def create_sales_order_validate(self):
        """Perform validation before creating a new sales order"""

        self.no_sales_order_validate()
        self.shopee_order_items_validate()

    def no_sales_order_validate(self):
        """Check if current shopee order already has a sales order"""

        if self.sales_order:
            frappe.throw(
                msg=f"Shopee order {self.name} already has a sales order {self.sales_order} matched",
            )

    def shopee_order_items_validate(self):
        """Check that all Shopee Order Items are matched with erpnext Item"""

        for order_item in self.order_items:
            if order_item.get_shopee_product().item is None:
                frappe.throw(
                    msg=f"Shopee product {order_item.get_shopee_product()} has not been matched with erpnext item",
                )

    def pre_create_sales_order(self, ignore_permissions=False):
        """Perform actions before creating a sales order, e.g. creating a customer and address, if none exists"""

        if not self.customer:
            self.create_customer_document(ignore_permissions=ignore_permissions)
            self.create_address_document(ignore_permissions=ignore_permissions)

            customer = self.get_customer_instance()
            address = self.get_address_instance()
            customer.add_address(address)

    def create_customer_document(self, ignore_permissions=False):
        """Create a new customer or update current customer document for the order's buyer"""

        self.get_customer_instance().update_or_insert(
            ignore_permissions=ignore_permissions
        )

    def create_address_document(self, ignore_permissions=False):
        """Create a new address or update current address document for the order's buyer"""

        self.get_address_instance().update_or_insert(
            ignore_permissions=ignore_permissions
        )

    def before_save(self):

        self.create_customer_document(ignore_permissions=True)
        self.create_address_document(ignore_permissions=True)

        customer = self.get_customer_instance()
        address = self.get_address_instance()

        customer.add_address(address, ignore_permissions=True)
        self.customer = customer.get_primary_key()
        self.address = address.get_primary_key()

    def before_insert(self):
        self.create_cancel_reason()
        self.create_payment_method()

    def create_cancel_reason(self):
        if not self.cancel_reason:
            return

        if frappe.db.exists("Shopee Cancel Reason", self.cancel_reason):
            return

        cancel_reason = frappe.new_doc("Shopee Cancel Reason")
        cancel_reason.cancel_status = self.cancel_reason
        cancel_reason.insert(ignore_permissions=True)

    def create_payment_method(self):
        if not self.payment_method:
            return

        if frappe.db.exists("Shopee Payment Method", self.payment_method):
            return

        payment_method = frappe.new_doc("Shopee Payment Method")
        payment_method.payment_type = self.payment_method
        payment_method.insert(ignore_permissions=True)
