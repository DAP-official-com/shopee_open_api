from .base import ShopeeResponseBaseClass
from shopee_open_api.exceptions import BadRequestError
from .product import Product
import frappe


class OrderItem(ShopeeResponseBaseClass):
    """
    This class represents each order item in the order. Very much like ERPNext's order item.
    """

    DOCTYPE = "Shopee Order Item"
    PRODUCT_DOCTYPE = "Shopee Product"
    ORDER_DOCTYPE = "Shopee Order"
    PARENT_FIELD = "shopee_order_items"

    def update_or_insert(self, ignore_permissions=False):
        """Update or insert the Shopee Order Item document in the database"""

        self.insert_product_if_not_existing(ignore_permissions=ignore_permissions)

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

    def insert_product_if_not_existing(self, ignore_permissions=False):
        """Insert Shopee Product document (not Shopee Product Item document) first if not existing"""

        if not self.is_product_existing_in_database:
            product_instance = self.get_product_instance()
            product_instance.update_or_insert(ignore_permissions=ignore_permissions)

    def get_product_instance(self):
        """
        Get Shopee Product object from Shopee Api.

        This needs to be done because the data returned from Shopee's order api is mininmal and not enough
        to create a Shopee Product or Shopee Order Item document
        """

        r = self.client.product.get_item_base_info(item_id_list=self.get_product_id())

        if r.get("error"):
            raise BadRequestError(r.get("message"))

        return Product(r["response"]["item_list"][0], shop_id=self.get_shop_id())

    @property
    def is_existing_in_database(self):
        """Check if order item exists in database"""

        return frappe.db.exists(
            self.DOCTYPE,
            {
                "parent": self.get_order_sn(),
                "shopee_product": self.make_product_primary_key(),
            },
        )

    @property
    def is_product_existing_in_database(self):
        """Check if Shopee Product document exists in the database"""

        return frappe.db.exists(self.PRODUCT_DOCTYPE, self.make_product_primary_key())

    def get_shop_id(self):
        return self.shop_id

    def get_order_sn(self):
        return self.order_sn

    def get_product_id(self):
        return self.item_id

    def get_model_id(self):
        """If the order item is a product without a variants, model_id value is 0"""
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
        """This is a child table and the primary key is generated. frappe.db.exists returns the primary key if found, not boolean"""

        return self.is_existing_in_database
