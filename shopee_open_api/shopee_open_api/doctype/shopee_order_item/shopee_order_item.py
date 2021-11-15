# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShopeeOrderItem(Document):
    def get_shopee_product(self):
        return frappe.get_doc("Shopee Product", self.shopee_product)
