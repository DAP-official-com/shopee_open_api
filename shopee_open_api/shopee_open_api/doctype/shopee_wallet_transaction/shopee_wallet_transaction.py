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

    def get_orders_for_withdrawal(self):
        if self.transaction_type != "WITHDRAWAL_CREATED":
            raise ValueError(
                "Method get_transaction_for_withdrawal can only be called with transaction type 'WITHDRAWAL_CREATED'"
            )

        amount_to_check = abs(self.amount)
        amount_to_ignore = self.current_balance

        previous_transaction = self.previous_transaction
        result = []

        # Ignore transactions contributing to current balance
        while amount_to_ignore > 0:

            if previous_transaction is None:
                break

            if "WITHDRAWAL" in previous_transaction.transaction_type:
                previous_transaction = previous_transaction.previous_transaction
                continue

            amount_to_ignore -= previous_transaction.amount

            # Include the partial amount of a transaction that contributes withdrawn amount
            if amount_to_ignore < 0:
                amount_to_check += amount_to_ignore
                result.append(
                    {
                        "transaction": previous_transaction.name,
                        "transaction_type": previous_transaction.transaction_type,
                        "order_sn": previous_transaction.order_sn,
                        "amount": abs(amount_to_ignore),
                        "split": True,
                    }
                )

            previous_transaction = previous_transaction.previous_transaction

        # Include transactions contributing withdrawn amount
        while amount_to_check > 0:

            if previous_transaction is None:
                break

            if "WITHDRAWAL" in previous_transaction.transaction_type:
                previous_transaction = previous_transaction.previous_transaction
                continue

            amount_to_check -= previous_transaction.amount

            if amount_to_check < 0:
                result.append(
                    {
                        "transaction": previous_transaction.name,
                        "transaction_type": previous_transaction.transaction_type,
                        "order_sn": previous_transaction.order_sn,
                        "amount": amount_to_check + previous_transaction.amount,
                        "split": True,
                    }
                )
            else:
                result.append(
                    {
                        "transaction": previous_transaction.name,
                        "transaction_type": previous_transaction.transaction_type,
                        "order_sn": previous_transaction.order_sn,
                        "amount": previous_transaction.amount,
                        "split": False,
                    }
                )

            previous_transaction = previous_transaction.previous_transaction

        return result

    @property
    def previous_transaction(self):
        """Get previous transaction of current transaction."""

        previous_transaction = frappe.get_all(
            "Shopee Wallet Transaction",
            filters={
                "shopee_shop": self.shopee_shop,
                "name": ["<", self.name],
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
                "name": [">", self.name],
            },
            pluck="name",
            limit_page_length=1,
            order_by="create_time",
        )

        if next_transaction:
            return frappe.get_doc("Shopee Wallet Transaction", next_transaction[0])
        return None
