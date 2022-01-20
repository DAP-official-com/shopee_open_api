# Copyright (c) 2022, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.stock.doctype.item.item import Item
from shopee_open_api.shopee_open_api.doctype.shopee_shop import shopee_shop


class ShopeeProduct(Document):
    @property
    def has_item(self) -> bool:
        """Check if this product has ERPNext item that matches with it."""

        return bool(self.item)

    def create_new_item_and_add_to_product(self) -> None:
        """Create a new ERPNext item and add to current product."""

        if self.has_item:
            raise ValueError(f"Shopee product {self} already has a product")

        item = self.create_new_item_from_product()
        self.add_item_to_product(item=item)

    def create_new_item_from_product(self) -> Item:
        """Create a new ERPNext item based on current product."""

        item = frappe.new_doc("Item")
        item.item_code = self.get_item_primary_key()
        item.item_name = self.item_name[:140]
        item.shopee_item_name = self.item_name
        item.standard_rate = self.current_price
        item.item_group = "Products"

        self.create_item_defaults(item)

        item.save()

        return item

    def create_item_defaults(self, item: Item) -> None:
        defaults = frappe.defaults.get_defaults() or {}

        item.append(
            "item_defaults",
            {
                "company": defaults.get("company"),
                "default_warehouse": self.get_shopee_shop_document()
                .get_warehouse()
                .name,
                "default_price_list": self.get_shopee_shop_document()
                .get_price_list()
                .name,
            },
        )

    def get_item(self):
        """Get ERPNext Item instance."""

        return frappe.get_doc("Item", self.get_item_primary_key())

    def get_item_primary_key(self) -> str:
        """Get a primary key for ERPNext item. Return current item name if the product is matched with an item, otherwise return a new name"""

        if self.item:
            return self.item

        return f"SH-{self.shopee_product_id}-{self.shopee_model_id}"

    def add_item_to_product(self, item=None) -> None:
        """Match an ERPNext item with current product"""

        self.item = item.name
        self.save()

    def get_shopee_shop_document(self) -> shopee_shop.ShopeeShop:
        """Get an instance of item's shop"""
        return frappe.get_doc("Shopee Shop", self.shopee_shop)
