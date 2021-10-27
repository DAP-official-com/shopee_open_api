from .base import ShopeeResponseBaseClass
from .product import Product
import frappe


class OrderItem(ShopeeResponseBaseClass):
    DOCTYPE = "Shopee Order Item"
    PRODUCT_DOCTYPE = "Shopee Product"
    ORDER_DOCTYPE = "Shopee Order"
    PARENT_FIELD = "shopee_order_items"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update_or_insert(self, ignore_permissions=False):
        if self.is_existing_in_database:
            order_item = frappe.get_doc(self.DOCTYPE, self.get_primary_key())
        else:
            order_item = frappe.get_doc(
                {
                    "doctype": self.DOCTYPE,
                    "parent": self.get_order_sn(),
                    "shopee_product": self.make_product_primary_key(),
                    "parenttype": self.ORDER_DOCTYPE,
                    "parentfield": self.PARENT_FIELD,
                }
            )

        order_item.qty = self.get_qty()
        order_item.model_original_price = self.get_model_original_price()
        order_item.model_discounted_price = self.get_model_discounted_price()
        order_item.save(ignore_permissions=ignore_permissions)

    @property
    def is_existing_in_database(self):
        return frappe.db.exists(
            self.DOCTYPE,
            {
                "parent": self.get_order_sn(),
                "shopee_product": self.make_product_primary_key(),
            },
        )

    @property
    def is_product_existing_in_database(self):
        return frappe.db.exists(self.PRODUCT_DOCTYPE, self.make_product_primary_key())

    def get_order_sn(self):
        return self.order_sn

    def get_product_id(self):
        return self.item_id

    def get_model_id(self):
        return self.model_id

    def make_product_primary_key(self):
        return f"{self.get_product_id()}-{self.get_model_id()}"

    def get_model_original_price(self):
        return self.model_original_price

    def get_model_discounted_price(self):
        return self.model_discounted_price

    def get_qty(self):
        return self.model_quantity_purchased

    def get_primary_key(self):
        return self.is_existing_in_database
