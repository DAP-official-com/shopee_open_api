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
        """
        Set the product id. This is neccessary for products with variants,
        because the attribute is returned with the product api, but not with the model api.
        """

        self.product_id = product_id

    def set_model_id(self, model_id):
        """
        Set the model id. This is neccessary for products with variants,
        because the attribute is returned with the product api, but not with the model api.
        """

        self.model_id = model_id

    def to_json(self):
        response = self.__dict__.copy()
        response.pop("product", None)
        response["product_primary_key"] = self.get_product_primary_key()
        response["values_text"] = self.get_values_as_str()
        return response

    def get_attribute_id(self) -> str:
        """Get Shopee attribute id as a string, because the type is Data"""

        return str(self.attribute_id)

    def get_original_attribute_name(self) -> str:
        """Get Shopee attribute name"""

        return self.original_attribute_name

    def get_is_mandatory(self) -> bool:
        """Check if this attribute is neccessary"""

        return self.is_mandatory

    def get_product_id(self) -> str:
        """Get product id as a string. The product id is saved as a Data type in the database."""

        return str(self.product_id)

    def get_model_id(self) -> str:
        """Get product id as a string. The model id is saved as a Data type in the database."""

        if self.model_id is not None:
            return str(self.model_id)
        return None

    def get_product_primary_key(self) -> str:
        """Get Shopee Product primary key for current product the attribute belongs to."""

        if self.model_id is not None:
            return f"{self.get_product_id()}-{self.get_model_id()}"
        return f"{self.get_product_id()}"

    def get_values_as_str(self) -> str:
        """Get all the values of current attribute in a single string"""

        return "|".join(
            [
                f"{value['original_value_name']}{value['value_unit']}"
                for value in self.attribute_value_list
            ]
        )
