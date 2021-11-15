# Copyright (c) 2022, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShopeeProduct(Document):
    @property
    def has_item(self) -> bool:
        return bool(self.item)

    def create_new_item_and_add_to_product(self) -> None:
        if self.has_item:
            raise ValueError(f"Shopee product {self} already has a product")

        item = self.create_new_item_from_product()
        self.add_item_to_product(item=item)

    def create_new_item_from_product(self):

        item = frappe.new_doc("Item")
        item.item_code = self.get_item_primary_key()
        item.item_name = self.item_name
        item.standard_rate = self.current_price
        item.item_group = "Products"

        item.save()

        return item

    def get_item(self):
        return frappe.get_doc("Item", self.get_item_primary_key())

    def get_item_primary_key(self) -> str:
        return f"SH-{self.shopee_product_id}-{self.shopee_model_id}"

    def add_item_to_product(self, item=None) -> None:
        self.item = item.name
        self.save()
