from .base import ShopeeResponseBaseClass
from shopee_open_api.utils.client import get_client_from_shop_id
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
        response["models"] = self.get_models()
        response["variations"] = self.get_variations()

        return response

    def update_or_insert(self):

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

        if self.has_model and not getattr(self, "model_id", False):
            return None

        if self.has_model:
            return 0 < frappe.db.count(
                self.DOCTYPE,
                {
                    "shopee_product_id": self.product_id,
                    "shopee_model_id": str(self.model_id),
                },
            )

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
        self.tier_variations = self.model_details["tier_variation"]

    def get_models(self):
        """Getter method for variant models"""

        return getattr(self, "models", [])

    def get_variations(self):
        """Getter method for variations"""

        return getattr(self, "variations", [])
