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

    def before_save(self):
        if self.submit_sales_order_automatically:
            self.create_sales_order_after_shopee_order_has_been_created = True

        if self.create_delivery_note_when_status_is_shipped:
            self.create_sales_order_after_shopee_order_has_been_created = True
            self.submit_sales_order_automatically = True

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

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_or_insert_price_list()

    def get_warehouse_name(self):
        return f"Shopee Shop {self.shop_id}"

    def after_delete(self):
        default_company = frappe.get_doc("Company", frappe.db.get_default("Company"))
        company_abbr = default_company.abbr

        warehouse_name = frappe.db.get_list(
            "Warehouse",
            filters={
                "warehouse_name": self.get_warehouse_name(),
                "parent_warehouse": f"Stores - {company_abbr}",
                "company": frappe.db.get_default("Company"),
            },
            pluck="name",
        )[0]

        frappe.get_doc("Warehouse", warehouse_name).delete()

    def get_warehouse(self):
        """Get an instance of a warehouse for this shop."""

        default_company = frappe.get_doc("Company", frappe.db.get_default("Company"))
        company_abbr = default_company.abbr

        warehouse_name = frappe.db.get_all(
            "Warehouse",
            filters={
                "warehouse_name": self.get_warehouse_name(),
                "parent_warehouse": f"Stores - {company_abbr}",
                "company": frappe.db.get_default("Company"),
            },
            pluck="name",
        )[0]

        return frappe.get_doc("Warehouse", warehouse_name)

    def get_price_list(self):

        self.update_or_insert_price_list()

        price_list_name = frappe.get_all(
            "Price List",
            filters={
                "shopee_shop": self.name,
            },
            pluck="name",
        )[0]

        return frappe.get_doc("Price List", price_list_name)

    def update_or_insert_price_list(self) -> None:
        """Create a price list for this shop"""

        if self.has_price_list():
            return

        price_list = frappe.new_doc("Price List")
        price_list.shopee_shop = self.name
        price_list.price_list_name = f"{self.shop_name} Price List ({self.name})"
        price_list.currency = frappe.db.get_default("Currency")
        price_list.selling = True
        price_list.save()

    def has_price_list(self) -> bool:
        return bool(
            frappe.db.exists(
                {
                    "doctype": "Price List",
                    "shopee_shop": self.name,
                }
            )
        )

    @property
    def is_set_to_create_draft_sales_order(self) -> bool:
        """Check if create draft sales order is set to True"""
        return self.create_sales_order_after_shopee_order_has_been_created == 1

    @property
    def is_set_to_submit_sales_order(self) -> bool:
        """Check if submit sales order is set to True"""
        return self.submit_sales_order_automatically == 1

    @property
    def is_set_to_create_delivery_note(self) -> bool:
        """Check if automatically create delivery note is set to True"""
        return self.create_delivery_note_when_status_is_shipped == 1
