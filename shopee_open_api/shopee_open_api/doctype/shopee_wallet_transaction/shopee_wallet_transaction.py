# Copyright (c) 2022, Dap Official and contributors
# For license information, please see license.txt

import enum
import frappe
from frappe.model.document import Document
from typing import List


class TransactionType(enum.Enum):
    ALL = "WITHDRAWAL%"
    REQUESTED_WITHDRAWAL = "WITHDRAWAL_CREATED"
    COMPLETED_WITHDRAWAL = "WITHDRAWAL_COMPLETED"


class ShopeeWalletTransaction(Document):
    @staticmethod
    def withdrawals_from_shop(
        shop, transaction_type: TransactionType
    ) -> List["ShopeeWalletTransaction"]:

        withdrawal_names = frappe.db.get_all(
            "Shopee Wallet Transaction",
            filters={
                "shopee_shop": shop.name,
                "transaction_type": ["like", transaction_type.value],
            },
            pluck="name",
        )

        return [
            frappe.get_doc("Shopee Wallet Transaction", name)
            for name in withdrawal_names
        ]

    @property
    def previous_transaction(self):
        """Get previous transaction of current transaction."""

        previous_transaction = frappe.get_all(
            "Shopee Wallet Transaction",
            filters={
                "shopee_shop": self.shopee_shop,
                "create_time": ["<", self.create_time],
            },
            pluck="name",
            limit_page_length=1,
            order_by="create_time desc",
        )

        if previous_transaction:
            return frappe.get_doc("Shopee Wallet Transaction", previous_transaction[0])
        return None

    @property
    def next_transaction(self):
        """Get the next transaction of current transaction."""

        next_transaction = frappe.get_all(
            "Shopee Wallet Transaction",
            filters={
                "shopee_shop": self.shopee_shop,
                "create_time": [">", self.create_time],
            },
            pluck="name",
            limit_page_length=1,
            order_by="create_time",
        )

        if next_transaction:
            return frappe.get_doc("Shopee Wallet Transaction", next_transaction[0])
        return None
