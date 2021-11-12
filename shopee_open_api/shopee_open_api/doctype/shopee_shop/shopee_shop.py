# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShopeeShop(Document):
    def before_insert(self):

        default_company = frappe.get_doc("Company", frappe.db.get_default("Company"))
        company_abbr = default_company.abbr

        # make the default Stores warehouse parent
        store_warehouse = frappe.get_doc("Warehouse", f"Stores - {company_abbr}")
        store_warehouse.is_group = True
        store_warehouse.save()

        # make a new warehouse of this shop
        self.create_warehouse_for_this_shop()

        self.warehouse = f"{self.get_warehouse_name()} - {company_abbr}"

    def create_warehouse_for_this_shop(self):

        default_company = frappe.get_doc("Company", frappe.db.get_default("Company"))
        company_abbr = default_company.abbr

        new_warehouse = frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": self.get_warehouse_name(),
                "parent_warehouse": f"Stores - {company_abbr}",
                "company": frappe.db.get_default("Company"),
            }
        )

        new_warehouse.insert()
        print(new_warehouse)

    def get_warehouse_name(self):
        return f"Shopee Shop {self.shop_id}"
