# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe
import time

from datetime import datetime, timedelta
from frappe.model.document import Document
from erpnext.accounts.doctype.account import account
from shopee_open_api.utils import client

from shopee_open_api.exceptions import BadRequestError


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
        self.get_or_create_shipping_fee_account()

    def before_save(self):
        if self.submit_sales_order_automatically:
            self.create_sales_order_after_shopee_order_has_been_created = True

        if self.create_delivery_note_when_status_is_shipped:
            self.create_sales_order_after_shopee_order_has_been_created = True
            self.submit_sales_order_automatically = True

        if not self.last_wallet_transaction_update_unix:
            self.set_last_wallet_transaction_update_unix(days_in_the_past=90)

        self.last_wallet_transaction_update_date = datetime.fromtimestamp(
            self.last_wallet_transaction_update_unix
        )

    def set_last_wallet_transaction_update_unix(self, days_in_the_past: int = 90):
        """Set last wallet tranasction update date"""
        unix_now = int(time.time())
        self.last_wallet_transaction_update_unix = unix_now - (
            days_in_the_past * 60 * 60 * 24
        )

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
                    "Account",
                    filters={"shopee_shop": self.name, "account_type": "Receivable"},
                    pluck="name",
                )[0],
            )

        parent_receivable_account = self.get_or_create_parent_receivable_account()
        next_account_number = None

        if parent_receivable_account.account_number:

            all_receivable_accounts = frappe.get_all(
                "Account",
                filters={"parent_account": parent_receivable_account.name},
                pluck="account_number",
            )

            account_numbers = [
                account_num.split(" - ")[1]
                for account_num in all_receivable_accounts
                if account_num is not None and " - " in account_num
            ]

            if not account_numbers:
                next_account_number = f"{parent_receivable_account.account_number} - 01"
            else:
                next_account_number = f"{parent_receivable_account.account_number} - {int(max(account_numbers)) + 1:02d}"

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
        return frappe.db.exists(
            {
                "doctype": "Account",
                "account_type": "Receivable",
                "shopee_shop": self.name,
            }
        )

    def get_or_create_parent_receivable_account(self) -> account.Account:
        """Create a parent receivable account named 'Shopee Receivable' if not exists."""

        if self.has_parent_receivable_account:
            return frappe.get_doc(
                "Account",
                frappe.get_all(
                    "Account",
                    filters={"account_name": "Shopee Receivable"},
                    pluck="name",
                )[0],
            )

        root_receivable_account = frappe.get_doc(
            "Account",
            frappe.get_all(
                "Account", filters={"account_name": "Accounts Receivable"}, pluck="name"
            )[0],
        )

        next_account_number = None

        if root_receivable_account.account_number:

            all_receivable_accounts = frappe.get_all(
                "Account",
                filters={"parent_account": root_receivable_account.name},
                pluck="account_number",
            )

            account_numbers = [
                account_num
                for account_num in all_receivable_accounts
                if account_num is not None
            ]

            next_account_number = int(max(account_numbers)) + 10

        new_account = frappe.new_doc("Account")
        new_account.parent_account = root_receivable_account.name
        new_account.account_number = next_account_number
        new_account.account_name = "Shopee Receivable"
        new_account.account_type = "Receivable"
        new_account.is_group = True
        new_account.insert()

        return new_account

    @property
    def has_parent_receivable_account(self) -> bool:
        """Check if the parent receivable account exists"""
        return frappe.db.exists(
            {"doctype": "Account", "account_name": "Shopee Receivable"}
        )

    def get_or_create_parent_direct_expense_account(self) -> account.Account:
        """Create a parent direct expense account named 'Shopee Receivable' if not exists."""

        if self.has_parent_direct_expense_account:
            return frappe.get_doc(
                "Account",
                frappe.get_all(
                    "Account",
                    filters={"account_name": "Shopee Direct Expenses"},
                    pluck="name",
                )[0],
            )

        root_direct_expense_account = frappe.get_doc(
            "Account",
            frappe.get_all(
                "Account", filters={"account_name": "Direct Expenses"}, pluck="name"
            )[0],
        )

        next_account_number = None

        if root_direct_expense_account.account_number:

            all_direct_expense_accounts = frappe.get_all(
                "Account",
                filters={"parent_account": root_direct_expense_account.name},
                pluck="account_number",
            )

            account_numbers = [
                account_num
                for account_num in all_direct_expense_accounts
                if account_num is not None
            ]

            next_account_number = int(max(account_numbers)) + 10

        new_account = frappe.new_doc("Account")
        new_account.parent_account = root_direct_expense_account.name
        new_account.account_number = next_account_number
        new_account.account_name = "Shopee Direct Expenses"
        new_account.account_type = "Expense Account"
        new_account.is_group = True
        new_account.insert()

        return new_account

    @property
    def has_parent_direct_expense_account(self) -> bool:
        return frappe.db.exists(
            {"doctype": "Account", "account_name": "Shopee Direct Expenses"}
        )

    def get_or_create_shipping_fee_account(self) -> account.Account:
        """Get or create an account for shipping fee."""
        parent_indirect_expense_account = (
            self.get_or_create_parent_indirect_expense_account()
        )
        if self.has_shipping_fee_account:
            return frappe.get_doc(
                "Account",
                frappe.get_all(
                    "Account",
                    filters={
                        "parent_account": parent_indirect_expense_account.name,
                        "account_name": f"Shipping Fee",
                    },
                    pluck="name",
                )[0],
            )

        parent_indirect_expense_account = (
            self.get_or_create_parent_indirect_expense_account()
        )
        next_account_number = None

        if parent_indirect_expense_account.account_number:

            all_shopee_indirect_expense_accounts = frappe.get_all(
                "Account",
                filters={"parent_account": parent_indirect_expense_account.name},
                pluck="account_number",
            )

            account_numbers = [
                account_num.split(" - ")[1]
                for account_num in all_shopee_indirect_expense_accounts
                if account_num is not None and " - " in account_num
            ]

            if not account_numbers:
                next_account_number = (
                    f"{parent_indirect_expense_account.account_number} - 01"
                )
            else:
                next_account_number = f"{parent_indirect_expense_account.account_number} - {int(max(account_numbers)) + 1:02d}"

        new_account = frappe.new_doc("Account")
        new_account.parent_account = parent_indirect_expense_account.name
        new_account.account_number = next_account_number
        new_account.account_name = f"Shipping Fee"
        new_account.account_type = "Expense Account"
        new_account.insert()

        return new_account

    @property
    def has_shipping_fee_account(self) -> bool:
        """Check if this shop already has an account for shipping fee."""
        parent_indirect_expense_account = (
            self.get_or_create_parent_indirect_expense_account()
        )

        return bool(
            frappe.db.exists(
                {
                    "doctype": "Account",
                    "account_name": f"Shipping Fee",
                    "parent_account": parent_indirect_expense_account.name,
                }
            )
        )

    def get_or_create_parent_indirect_expense_account(self) -> account.Account:
        """Create a parent indirect expense account named 'Shopee Receivable' if not exists."""

        if self.has_parent_indirect_expense_account:
            return frappe.get_doc(
                "Account",
                frappe.get_all(
                    "Account",
                    filters={"account_name": "Shopee Indirect Expenses"},
                    pluck="name",
                )[0],
            )

        root_indirect_expense_account = frappe.get_doc(
            "Account",
            frappe.get_all(
                "Account", filters={"account_name": "Indirect Expenses"}, pluck="name"
            )[0],
        )

        next_account_number = None

        if root_indirect_expense_account.account_number:

            all_indirect_expense_accounts = frappe.get_all(
                "Account",
                filters={"parent_account": root_indirect_expense_account.name},
                pluck="account_number",
            )

            account_numbers = [
                account_num
                for account_num in all_indirect_expense_accounts
                if account_num is not None
            ]

            next_account_number = int(max(account_numbers)) + 1

        new_account = frappe.new_doc("Account")
        new_account.parent_account = root_indirect_expense_account.name
        new_account.account_number = next_account_number
        new_account.account_name = "Shopee Indirect Expenses"
        new_account.account_type = "Expense Account"
        new_account.is_group = True
        new_account.insert()

        return new_account

    @property
    def has_parent_indirect_expense_account(self) -> bool:
        return frappe.db.exists(
            {"doctype": "Account", "account_name": "Shopee Indirect Expenses"}
        )

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

    @property
    def client(self):
        return client.get_client_from_shop_id(self.name)

    def update_wallet_transactions(self) -> None:

        page_size = 100
        current_unix = int(time.time())

        for start_unix in range(
            self.last_wallet_transaction_update_unix, current_unix, 60 * 60 * 24
        ):

            end_unix = start_unix + (60 * 60 * 24)

            page_no = 0

            while True:
                r = self.client.payment.get_wallet_transaction_list(
                    page_size=page_size,
                    page_no=page_no,
                    create_time_from=start_unix,
                    create_time_to=end_unix,
                )

                if r.get("error"):
                    raise BadRequestError(
                        f"error: {r.get('error')}. error_message: {r.get('message')}."
                    )

                transactions = r.get("response", {}).get("transaction_list", [])

                ## save transactions to the database
                for transaction in transactions:

                    if frappe.db.exists(
                        "Shopee Wallet Transaction", transaction["transaction_id"]
                    ):
                        continue

                    new_transaction = frappe.get_doc(
                        doctype="Shopee Wallet Transaction",
                        shopee_shop=self.name,
                        **transaction,
                    )
                    new_transaction.insert()
                    frappe.db.commit()

                has_more = r.get("response", {}).get("more")

                if not has_more:
                    self.last_wallet_transaction_update_unix = end_unix
                    self.save()
                    frappe.db.commit()
                    break

                page_no += 1
