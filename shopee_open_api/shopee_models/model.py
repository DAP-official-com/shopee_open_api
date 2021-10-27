from .base import ShopeeResponseBaseClass
import frappe


class Model(ShopeeResponseBaseClass):

    DOCTYPE = "Shopee Product"

    def make_primary_key(self):
        return f"{self.product.get_product_id()}-{self.get_model_id()}"

    def make_variant_string(self):
        return ",".join(
            [variant["variation"]["option"] for variant in self.get_variations()]
        )

    def get_variations(self):
        return self.variations

    def make_product_name(self):
        return f"{self.product.item_name} ({self.make_variant_string()})"

    def update_or_insert(self):
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

        shopee_product.save()

    @property
    def is_existing_in_database(self):
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
        return str(self.model_id)
