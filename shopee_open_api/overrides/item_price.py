import frappe

from erpnext.stock.doctype.item_price.item_price import ItemPrice


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
