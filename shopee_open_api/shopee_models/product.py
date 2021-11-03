from .base import ShopeeResponseBaseClass
from shopee_open_api.utils.client import get_client_from_shop_id
from .model import Model
from .stock import Stock
from .product_attribute import ProductAttribute
import copy
import frappe

ITEM_STATUSES = ["NORMAL", "BANNED", "DELETED", "UNLIST"]


class Product(ShopeeResponseBaseClass):
    """This class represents a shopee product with additional methods"""

    DOCTYPE = "Shopee Product"

    def __str__(self):
        return f"{super().__str__()} {self.item_name}"

    def make_primary_key(self):
        return f"{self.get_product_id()}-{self.get_model_id()}"

    def to_json(self):

        response = self.__dict__
        response["is_existing_in_database"] = self.is_existing_in_database
        response["main_image"] = self.get_main_image()
        response.pop("models", False)

        return response

    def update_or_insert(self, ignore_permissions=False):

        if self.has_model and self.get_models():
            for model in self.get_models():
                model.update_or_insert(ignore_permissions=ignore_permissions)
            return

        if self.is_existing_in_database:
            shopee_product = frappe.get_doc(
                self.DOCTYPE,
                self.make_primary_key(),
            )
        else:
            shopee_product = frappe.get_doc(
                doctype=self.DOCTYPE,
                shopee_product_id=self.get_product_id(),
                shopee_model_id=self.get_model_id(),
                shopee_shop=self.get_shop_id(),
            )

        shopee_product.item_status = self.item_status
        shopee_product.category = self.get_category_id()
        shopee_product.weight = self.get_weight()
        shopee_product.item_name = self.item_name
        shopee_product.image = self.get_main_image()
        shopee_product.brand = self.get_brand_name()

        self.reset_product_attributes(product_object=shopee_product)
        self.add_product_attributes(product_object=shopee_product)

        shopee_product.save(ignore_permissions=ignore_permissions)

    @property
    def is_existing_in_database(self) -> bool:

        if (
            frappe.db.count(
                self.DOCTYPE,
                {
                    "shopee_product_id": self.get_product_id(),
                },
            )
            == 0
        ):
            return False

        if self.has_model and self.get_models():
            for model in self.get_models():
                if not model.is_existing_in_database:
                    return False
            return True

        return 0 < frappe.db.count(
            self.DOCTYPE,
            {
                "shopee_product_id": self.get_product_id(),
                "shopee_model_id": "0",
            },
        )

    @property
    def client(self):
        """Get Shopee client"""
        return get_client_from_shop_id(self.get_shop_id())

    def reset_product_attributes(self, product_object):
        product_object.attributes = []

    def add_product_attributes(self, product_object):
        for attribute in self.get_attributes():
            new_attribute = product_object.append("attributes", {})
            new_attribute.attribute_id = attribute.get_attribute_id()

            original_attribute_name = attribute.get_original_attribute_name()
            new_attribute.original_attribute_name = original_attribute_name

            new_attribute.is_mandatory = attribute.get_is_mandatory()
            new_attribute.values = attribute.get_values_as_str()

    def retrieve_model_details(self):
        """Fetch variant details from Shopee"""

        self.model_details = self.client.product.get_model_list(item_id=self.item_id)[
            "response"
        ]
        self.models = self.model_details["model"]

    def get_models(self):
        """Getter method for variant models"""
        if self.has_model and not hasattr(self, "models"):
            self.instantiate_models()

        return getattr(self, "models", [])

    def instantiate_models(self):
        """Instantiate all models for current product."""

        if not self.has_model:
            return

        if not hasattr(self, "model_details"):
            self.retrieve_model_details()

        for model in self.model_details["model"]:
            model["variations"] = []

            for variation_index, option_index in enumerate(model["tier_index"]):

                variation = self.model_details["tier_variation"][variation_index]

                variation_details = {}
                variation_details["name"] = variation["name"]

                variation_details["variation"] = variation["option_list"][option_index]

                model["variations"].append(variation_details)

        self.models = [Model(model, product=self) for model in self.get_models()]

    def get_main_image(self) -> str:
        return self.image["image_url_list"][0]

    def get_shop_id(self) -> str:
        return str(self.shop_id)

    def get_category_id(self):
        return str(self.category_id)

    def get_weight(self) -> float:
        return float(self.weight)

    def get_product_id(self) -> str:
        return str(self.item_id)

    def get_model_id(self) -> str:
        if self.has_model:
            return str(self.model_id)
        return str(0)

    def get_brand_name(self):
        return self.brand["original_brand_name"]

    def get_inventory(self):
        return [Stock(inventory, product=self) for inventory in self.stock_info]

    def get_attributes(self):

        if not hasattr(self, "attribute_list"):
            return []

        attributes = [
            ProductAttribute(attribute, product_id=self.get_product_id())
            for attribute in self.attribute_list
        ]

        return attributes
