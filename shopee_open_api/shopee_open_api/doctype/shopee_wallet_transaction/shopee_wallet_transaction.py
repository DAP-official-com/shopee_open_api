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
    def pending_withdrawals_to_process():
        """Get all withdrawal transactions that needs to process payment."""
        return [
            frappe.get_doc("Shopee Wallet Transaction", name)
            for name in frappe.get_all(
                "Shopee Wallet Transaction",
                filters={
                    "transaction_type": TransactionType.REQUESTED_WITHDRAWAL.value,
                    "payment_processed": 0,
                },
                pluck="name",
            )
        ]

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

    def get_withdrawal_request(self):
        """Get withdrawal request that corresponds to withdrawal complete"""
        if self.transaction_type != TransactionType.COMPLETED_WITHDRAWAL.value:
            return None

        previous_withdrawal_requests = frappe.get_all(
            "Shopee Wallet Transaction",
            filters={
                "shopee_shop": self.shopee_shop,
                "transaction_type": TransactionType.REQUESTED_WITHDRAWAL.value,
                "create_time": ("<=", self.create_time),
            },
            pluck="name",
        )

        if previous_withdrawal_requests:
            return frappe.get_doc(
                "Shopee Wallet Transaction", previous_withdrawal_requests[0]
            )
        return None

    def get_withdrawal_complete(self):
        """Get withdrawal complete that corresponds to current withdrawal request"""
        if self.transaction_type != TransactionType.REQUESTED_WITHDRAWAL.value:
            return None

        later_withdrawal_completes = frappe.get_all(
            "Shopee Wallet Transaction",
            filters={
                "shopee_shop": self.shopee_shop,
                "transaction_type": TransactionType.COMPLETED_WITHDRAWAL.value,
                "create_time": (">=", self.create_time),
            },
            order_by="create_time asc",
            pluck="name",
        )

        if later_withdrawal_completes:
            return frappe.get_doc(
                "Shopee Wallet Transaction", later_withdrawal_completes[0]
            )
        return None

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
                        "transaction": previous_transaction,
                        "split": True,
                        "amount": abs(amount_to_ignore),
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
                        "transaction": previous_transaction,
                        "split": True,
                        "amount": amount_to_check + previous_transaction.amount,
                    }
                )
            else:
                result.append(
                    {
                        "transaction": previous_transaction,
                        "split": False,
                        "amount": previous_transaction.amount,
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

    def get_shopee_order_document(self):
        """Get an instance of Shopee Order from attribute order_sn."""

        if not self.order_sn:
            return None
        if not frappe.db.exists("Shopee Order", self.order_sn):
            return None
        return frappe.get_doc("Shopee Order", self.order_sn)
