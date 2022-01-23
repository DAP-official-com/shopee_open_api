import frappe

from erpnext.stock.doctype.item_price.item_price import ItemPrice
from shopee_open_api.utils.client import get_client_from_shop
from shopee_open_api.apis import product


class CustomItemPrice(ItemPrice):
    """Custom item price class to ERPNext Item Price doctype"""

    def validate(self, *args, **kwargs):
        super().validate(*args, **kwargs)

        if self.shopee_product:
            if (
                frappe.db.count(
                    "Item Price",
                    {
                        "shopee_product": self.shopee_product,
                        "name": ["!=", self.name],
                    },
                )
                > 0
            ):
                frappe.throw(
                    f"Only one item price can be matched with shopee product {self.shopee_product}"
                )

    def before_save(self, *args, **kwargs):
        super().before_save(*args, **kwargs)

        if not self.shopee_product:
            self.shopee_model_id = None
            return

        doc_before_save = self.get_doc_before_save()

        if doc_before_save is None:
            return

        if doc_before_save.price_list_rate == self.price_list_rate:
            return

        self.update_price_on_shopee()
        product.reload_product_details_from_shopee(
            self.get_shopee_product_document().name
        )

    def update_price_on_shopee(self):
        client = self.get_shopee_client()

        r = client.product.update_price(
            item_id=int(self.get_shopee_product_document().shopee_product_id),
            price_list=[
                {
                    "model_id": int(self.shopee_model_id),
                    "original_price": self.price_list_rate,
                },
            ],
        )

        if r.get("message", None):
            frappe.throw(r.get("message"))

    def get_shopee_client(self):
        """Get a Shopee API client for the shop owning shopee product of this item price."""

        return get_client_from_shop(self.get_shopee_shop_document())

    def get_shopee_shop_document(self):
        """Get a document of the Shopee Shop for this item price"""

        if self.get_shopee_product_document() is None:
            return None
        return self.get_shopee_product_document().get_shopee_shop_document()

    def get_shopee_product_document(self):
        """Get a document of the Shopee Product for this item price"""
        if not self.shopee_product:
            return None

        return frappe.get_doc("Shopee Product", self.shopee_product)
