from .base import ShopeeResponseBaseClass
from .stock import Stock
import frappe


class Model(ShopeeResponseBaseClass):
    """
    This class represents each model of Shopee product. A product without variants does not have a model.
    One model is treated as one Shopee Product document.
    """

    DOCTYPE = "Shopee Product"

    def to_json(self):
        data = self.__dict__.copy()
        data.pop("product", False)
        return data

    def make_primary_key(self):
        return f"{self.product.get_product_id()}-{self.get_model_id()}"

    def make_variant_string(self):
        """Make a variant string. E.g. long,brown, long,grey"""
        return ",".join(
            [variant["variation"]["option"] for variant in self.get_variations()]
        )

    def get_variations(self):
        """Get all the variations of the product"""

        return self.variations

    def make_product_name(self):
        """Make a primary key (name) for this model"""

        return f"{self.product.item_name} ({self.make_variant_string()})"

    def update_or_insert(self, ignore_permissions=False):
        """Update existing document or insert a new Shopee Product to the database"""

        if self.is_existing_in_database:
            shopee_product = frappe.get_doc(
                self.DOCTYPE,
                self.make_primary_key(),
            )
        else:
            shopee_product = frappe.get_doc(
                doctype=self.DOCTYPE,
                shopee_product_id=self.product.get_product_id(),
                shopee_model_id=self.get_model_id(),
                shopee_shop=self.product.get_shop_id(),
            )

        shopee_product.item_status = self.product.item_status
        shopee_product.category = self.product.get_category_id()
        shopee_product.weight = self.product.get_weight()
        shopee_product.item_name = self.make_product_name()
        shopee_product.image = self.product.get_main_image()
        shopee_product.brand = self.product.get_brand_name()
        shopee_product.currency = self.get_currency()
        shopee_product.original_price = self.get_original_price()
        shopee_product.current_price = self.get_current_price()

        self.product.reset_product_attributes(product_object=shopee_product)
        self.product.add_product_attributes(product_object=shopee_product)

        self.update_product_stock(product_object=shopee_product)

        shopee_product.save(ignore_permissions=ignore_permissions)

    @property
    def is_existing_in_database(self):
        """Check if the model is already in the database"""

        return 0 < frappe.db.count(
            self.DOCTYPE,
            {
                "shopee_product_id": self.product.get_product_id(),
                "shopee_model_id": self.get_model_id(),
            },
        )

    def __str__(self):
        return f"{super().__str__()} {self.make_product_name()}"

    def get_model_id(self) -> str:
        """Get a model id as a string, since the field type in the Doctype is data."""

        return str(self.model_id)

    def get_attributes(self):
        """
        Get all the attributes for this product and update the attributes with a model id to
        create or update each product's attributes
        """

        attributes = self.product.get_attributes()

        for attribute in attributes:
            attribute.set_model_id(self.get_model_id())

        return attributes

    def get_inventories(self):
        """Get the inventories of current model."""

        return [Stock(inventory, product=self.product) for inventory in self.stock_info]

    def get_currency(self):
        """Get currency code provided by Shopee, or fallback to the site's default currency"""

        return self.price_info[0].get("currency", frappe.db.get_default("Currency"))

    def get_original_price(self):
        """Get the original price of the model. If there is no discount, current price and origianal price are the same"""

        return float(self.price_info[0].get("original_price"))

    def get_current_price(self):
        """Get currently selling price of the model."""

        return float(self.price_info[0].get("current_price"))

    def update_product_stock(self, product_object):
        """Update the stock level of the model."""

        current_stocks = product_object.get("stock_details", [])
        shopee_stocks = self.get_inventories()

        shopee_stock_types = [stock.get_stock_type() for stock in shopee_stocks]

        for current_stock in current_stocks:
            """Remove stocks in the database that no longer exists on shopee"""
            if current_stock.stock_type not in shopee_stock_types:
                product_object.stock_details.remove(current_stock)

        for stock in shopee_stocks:

            current_stocks = product_object.get(
                "stock_details", {"stock_type": stock.get_stock_type()}
            )

            if current_stocks:
                for current_stock in current_stocks:
                    current_stock.current_stock = stock.get_current_stock()
                    current_stock.normal_stock = stock.get_normal_stock()
                    current_stock.reserved_stock = stock.get_reserved_stock()
            else:
                new_stock_details = product_object.append("stock_details", {})
                new_stock_details.stock_type = stock.get_stock_type()
                new_stock_details.stock_type_name = stock.get_stock_type_name()
                new_stock_details.current_stock = stock.get_current_stock()
                new_stock_details.normal_stock = stock.get_normal_stock()
                new_stock_details.reserved_stock = stock.get_reserved_stock()
