# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from shopee_open_api.shopee_models.customer import Customer
from shopee_open_api.shopee_models.address import Address


class ShopeeOrder(Document):
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
        return Address.from_shopee_address(**self.address_detail)
