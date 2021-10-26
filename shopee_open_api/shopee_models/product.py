from .base import ShopeeResponseBaseClass
from shopee_open_api.utils.client import get_client_from_shop_id
from .model import Model
import copy
import frappe


class Product(ShopeeResponseBaseClass):
    """This class represents a shopee product with additional methods"""

    DOCTYPE = "Shopee Product"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parse_attributes()

    def make_primary_key(self):
        return f"{self.product_id}-{self.model_id if self.has_model else 0}"

    def parse_attributes(self):
        self.shope_ip = str(self.shop_id)
        self.category_id = str(self.category_id)
        self.weight = float(self.weight)
        self.product_id = str(self.item_id)

    def to_json(self):

        response = self.__dict__
        response["is_existing_in_database"] = self.is_existing_in_database
        response.pop("models", False)

        return response

    def update_or_insert(self):

        if self.has_model and self.get_models():
            for model in self.get_models():
                model.update_or_insert()
            return

        if self.is_existing_in_database:
            shopee_product = frappe.get_doc(
                self.DOCTYPE,
                self.make_primary_key(),
            )
        else:
            shopee_product = frappe.get_doc(
                doctype=self.DOCTYPE,
                shopee_product_id=self.product_id,
                shopee_model_id=str(self.model_id) if self.has_model else "0",
                shopee_shop=self.shop_id,
            )

        shopee_product.item_status = self.item_status
        shopee_product.category = self.category_id
        shopee_product.weight = self.weight
        shopee_product.item_name = self.item_name

        shopee_product.save()

    @property
    def is_existing_in_database(self) -> bool:

        if (
            frappe.db.count(
                self.DOCTYPE,
                {
                    "shopee_product_id": self.product_id,
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
                "shopee_product_id": self.product_id,
                "shopee_model_id": "0",
            },
        )

    @property
    def client(self):
        """Get Shopee client"""
        return get_client_from_shop_id(self.shop_id)

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
