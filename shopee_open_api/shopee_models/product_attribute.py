from .base import ShopeeResponseBaseClass
import frappe


class ProductAttribute(ShopeeResponseBaseClass):
    """A class representing a product attribute"""

    DOCTYPE = "Shopee Product Attribute"

    def __init__(self, *args, **kwargs):
        self.product_id = kwargs.pop("product_id", None)
        self.model_id = kwargs.pop("model_id", None)
        super().__init__(*args, **kwargs)

    def set_product_id(self, product_id):
        self.product_id = product_id

    def set_model_id(self, model_id):
        self.model_id = model_id

    def to_json(self):
        response = self.__dict__.copy()
        response.pop("product", None)
        response["product_primary_key"] = self.get_product_primary_key()
        response["values_text"] = self.get_values_as_str()
        return response

    def get_attribute_id(self):
        return str(self.attribute_id)

    def get_original_attribute_name(self):
        return self.original_attribute_name

    def get_is_mandatory(self):
        return self.is_mandatory

    def get_product_id(self):
        return str(self.product_id)

    def get_model_id(self):
        if self.model_id is not None:
            return str(self.model_id)
        return None

    def get_product_primary_key(self):
        if self.model_id is not None:
            return f"{self.get_product_id()}-{self.get_model_id()}"
        return f"{self.get_product_id()}"

    def get_values_as_str(self):
        return "|".join(
            [
                f"{value['original_value_name']}{value['value_unit']}"
                for value in self.attribute_value_list
            ]
        )
