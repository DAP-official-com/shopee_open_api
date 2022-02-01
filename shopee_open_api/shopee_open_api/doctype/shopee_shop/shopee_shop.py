# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.accounts.doctype.account import account


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

    def after_insert(self):
        # make a new receivable account for this shop
        self.create_receivable_account()

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

    def get_receivable_account(self) -> account.Account:
        return self.create_receivable_account()

    def create_receivable_account(self) -> account.Account:
        """Create new receivable account for this shop."""

        if self.has_receivable_account:
            return frappe.get_doc(
                "Account",
                frappe.get_all(
                    "Account", filters={"shopee_shop": self.name}, pluck="name"
                )[0],
            )

        parent_receivable_account = frappe.get_doc(
            "Account",
            frappe.get_all(
                "Account", filters={"account_name": "Accounts Receivable"}, pluck="name"
            )[0],
        )

        next_account_number = None

        if parent_receivable_account.account_number:

            all_receivable_accounts = frappe.get_all(
                "Account",
                filters={"parent_account": parent_receivable_account.name},
                pluck="account_number",
            )

            account_numbers = [
                account_num
                for account_num in all_receivable_accounts
                if account_num is not None
            ]

            next_account_number = int(max(account_numbers)) + 10

        new_account = frappe.new_doc("Account")
        new_account.parent_account = parent_receivable_account.name
        new_account.account_number = next_account_number
        new_account.account_name = self.shop_name
        new_account.shopee_shop = self.name
        new_account.account_type = "Receivable"
        new_account.insert()

        return new_account

    @property
    def has_receivable_account(self):
        """Check if this shop already has a receivable account."""
        return frappe.db.exists({"doctype": "Account", "shopee_shop": self.name})

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

    @property
    def is_set_to_create_sales_invoice(self) -> bool:
        """Check if automatically create sales invoice is set to True."""
        return self.create_sales_invoice_when_status_is_completed == 1
