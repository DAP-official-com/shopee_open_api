# Copyright (c) 2022, Dap Official and contributors
# For license information, please see license.txt

import erpnext
import frappe

from erpnext.stock.doctype.item.item import Item
from erpnext.stock.doctype.item_price.item_price import ItemPrice
from frappe.model.document import Document
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
        # item.standard_rate = self.current_price
        item.item_group = "Products"

        self.create_item_defaults(item=item)
        item.save()
        self.create_item_price(item=item)

        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Receipt"
        stock_entry.to_warehouse = frappe.get_all(
            "Warehouse",
            filters={
                "warehouse_name": self.get_shopee_shop_document().get_warehouse_name(),
            },
            pluck="name",
        )[0]
        stock_entry_detail = stock_entry.append("items", {})
        stock_entry_detail.item_code = self.get_item_primary_key()
        stock_entry_detail.qty = 1000
        stock_entry_detail.basic_rate = 20

        stock_entry.insert()
        stock_entry.submit()

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

    def create_item_price(self, item: Item):
        """Create item price and set shopee_product field"""

        item_price = frappe.get_doc(
            {
                "doctype": "Item Price",
                "price_list": self.get_shopee_shop_document().get_price_list().name,
                "item_code": item.name,
                "uom": item.stock_uom,
                "brand": item.brand,
                "currency": erpnext.get_default_currency(),
                "price_list_rate": self.current_price,
                "shopee_product": self.name,
            }
        )
        item_price.insert()

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

    def get_item_price(self) -> ItemPrice:
        """Get an instance of an Item Price belonging to this product."""
        return frappe.get_doc(
            "Item Price",
            frappe.get_all(
                "Item Price",
                filters={
                    "shopee_product": self.name,
                },
                pluck="name",
            )[0],
        )

    def has_item_price(self) -> bool:
        """Check if there is an Item Price document belonging to this product."""

        return bool(
            frappe.db.exists(
                {
                    "doctype": "Item Price",
                    "shopee_product": self.name,
                }
            )
        )
