# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from shopee_open_api.shopee_models.customer import Customer


class ShopeeOrder(Document):
    @property
    def customer_detail(self):

        customer = {}

        # data for Customer Doctype
        customer["customer_type"] = "Individual"
        customer["customer_group"] = "Individual"
        customer["address_type"] = "Postal"
        customer["customer_name"] = self.recipient_name
        customer["territory"] = frappe.db.get_default("Country")
        customer["username"] = self.buyer_username
        customer["user_id"] = self.buyer_user_id
        customer["shopee_user_id"] = self.buyer_user_id
        customer["mobile_no"] = self.recipient_phone

        return customer

    def get_customer_instance(self):
        return Customer.from_shopee_customer(**self.customer_detail)
