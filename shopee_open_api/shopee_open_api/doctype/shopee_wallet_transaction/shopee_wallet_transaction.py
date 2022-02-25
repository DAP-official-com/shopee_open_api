# Copyright (c) 2022, Dap Official and contributors
# For license information, please see license.txt

import enum
import frappe
import inspect
from frappe.model.document import Document
from typing import List

from shopee_open_api.exceptions import PaymentProcessingError
from shopee_open_api.utils.datetime import datetime_from_unix
from shopee_open_api.shopee_models.order import Order


class TransactionType(enum.Enum):
    ALL = "WITHDRAWAL%"
    REQUESTED_WITHDRAWAL = "WITHDRAWAL_CREATED"
    COMPLETED_WITHDRAWAL = "WITHDRAWAL_COMPLETED"
    ESCROW_VERIFIED_ADD = "ESCROW_VERIFIED_ADD"
    ADJUSTMENT_MINUS = "ADJUSTMENT_MINUS"
    ADJUSTMENT_ADD = "ADJUSTMENT_ADD"


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

    def process_payment(self) -> None:
        """
        Process transactions under current withdrawal request.

        Each time there is a withdrawal request, there are multiple transactions that contribute to the total amount.
        A withdrawal request transaction is accompanied by a withdrawl complete transaction, usually a day after.
        That's why we check that the withdrawal complete transaction is present before processing the request.

        For transaction type "ESCROW_VERIFIED_ADD", the amount will be the final amount paid by Shopee to seller,
        excluding the transaction fee. Since the transaction fee was recorded in sales invoice as commission, it does
        not reflect on the actual account yet, and that the receivable amount will be higher than the escrow amount.
        Our approach is to collect the full payment, then record transaction fee as an expense.
        However, some orders can be paid partially twice, we cannot collect the transaction fee both times. Hence, the transaction fee
        paid condition was checked.

        There are also some orders that do not exist in the database, or that they do not have sales invoice yet
        due to myriad reasons. We record those transactions as indirect income and ignore the transaction fee altogether.

        For transaction types "ADJUSTMENT_ADD" and "ADJUSTMENT_MINUS", they are recorded as indirect income,
        either on credit or debit depending on the positivity or negativity of the amount.

        Once all the transactions are recorded, we need to record payment for the transaction fee amount paid by end-customer
        to Shopee, so that the Debit must equal Credit.
        """

        if self.payment_processed:
            return

        if self.transaction_type != "WITHDRAWAL_CREATED":
            raise PaymentProcessingError(
                f"Method {inspect.stack()[0][3]} can only be called with transaction type 'WITHDRAWAL_CREATED'"
            )

        withdrawal_complete_transaction = self.get_withdrawal_complete()
        if withdrawal_complete_transaction is None:
            return

        shopee_shop = self.get_shopee_shop_document()
        shops_cash_account = shopee_shop.get_or_create_cash_account()
        shops_receivable_account = shopee_shop.get_receivable_account()
        shops_indirect_income_account = (
            shopee_shop.get_or_create_indirect_income_account()
        )

        payment_datetime = datetime_from_unix(
            withdrawal_complete_transaction.create_time
        )

        total_balance = {"debit": 0, "credit": 0}

        transactions_to_process = self.get_orders_for_withdrawal()

        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.posting_date = payment_datetime.date()
        journal_entry.user_remark = f"""Withdrawal Request ID: {self.name}\nWithdrawal Complete ID: {withdrawal_complete_transaction.name}"""

        journal_transaction = journal_entry.append("accounts", {})
        journal_transaction.account = shops_cash_account.name
        journal_transaction.debit_in_account_currency = abs(self.amount)
        journal_transaction.user_remark = f"""Transaction Type: {self.transaction_type}\nTransaction id: {self.name}\nOrder SN: {self.order_sn}\nTransaction reason: {self.reason}"""

        total_balance["debit"] = +abs(self.amount)

        for transaction in transactions_to_process:
            journal_transaction = journal_entry.append("accounts", {})

            if (
                transaction.get("transaction").transaction_type
                == TransactionType.ESCROW_VERIFIED_ADD.value
            ):
                order_sn = transaction.get("transaction").order_sn

                if (
                    frappe.db.exists("Shopee Order", order_sn)
                    and frappe.get_doc("Shopee Order", order_sn).sales_invoice
                ):
                    shopee_order = frappe.get_doc("Shopee Order", order_sn)
                    journal_transaction.account = shops_receivable_account.name
                    journal_transaction.party_type = "Customer"
                    journal_transaction.party = shopee_order.customer

                    if shopee_order.transaction_fee_paid:
                        amount_to_credit = transaction.get("amount")
                    else:
                        amount_to_credit = (
                            transaction.get("amount")
                            + shopee_order.seller_transaction_fee
                        )
                        shopee_order.transaction_fee_paid = True
                        shopee_order.save()

                    journal_transaction.credit_in_account_currency = amount_to_credit
                else:
                    journal_transaction.account = shops_indirect_income_account.name
                    amount_to_credit = transaction.get("amount")
                    journal_transaction.credit_in_account_currency = amount_to_credit
                    journal_transaction.party_type = "Supplier"
                    journal_transaction.party = "Shopee"

                total_balance["credit"] += amount_to_credit

            if (
                transaction.get("transaction").transaction_type
                == TransactionType.ADJUSTMENT_ADD.value
            ):
                journal_transaction.account = shops_indirect_income_account.name
                amount_to_credit = transaction.get("amount")
                journal_transaction.credit_in_account_currency = amount_to_credit
                total_balance["credit"] += amount_to_credit

            if (
                transaction.get("transaction").transaction_type
                == TransactionType.ADJUSTMENT_MINUS.value
            ):
                journal_transaction.account = shops_indirect_income_account.name
                amount_to_credit = transaction.get("amount")
                journal_transaction.credit_in_account_currency = amount_to_credit
                total_balance["credit"] += amount_to_credit

            journal_transaction.user_remark = f"""Transaction Type: {transaction.get("transaction").transaction_type}\nTransaction id: {transaction.get("transaction").name}\nOrder SN: {transaction.get("transaction").order_sn}\nTransaction reason: {transaction.get("transaction").reason}"""

            print(total_balance)

        """Pay remaining amount as commission (transaction fee)"""
        balance_difference = total_balance.get("credit") - total_balance.get("debit")
        if balance_difference != 0:
            journal_transaction = journal_entry.append("accounts", {})
            journal_transaction.account = shopee_shop.get_sales_expenses_account().name
            journal_transaction.party_type = "Supplier"
            journal_transaction.party = "Shopee"
            journal_transaction.debit_in_account_currency = balance_difference
            journal_transaction.user_remark = "Commission (Transaction fee)"

            total_balance["debit"] += balance_difference

        print(total_balance)

        withdrawal_complete_transaction.payment_processed = True
        withdrawal_complete_transaction.payment_processed_datetime = frappe.utils.now()

        self.payment_processed = True
        self.payment_processed_datetime = frappe.utils.now()
        self.save()

        journal_entry.insert()
        journal_entry.submit()
        journal_entry.save()

    def get_shopee_order_document(self):
        """Get an instance of Shopee Order from attribute order_sn."""

        if not self.order_sn:
            return None
        if not frappe.db.exists("Shopee Order", self.order_sn):
            return None
        return frappe.get_doc("Shopee Order", self.order_sn)

    def get_shopee_shop_document(self):
        """Get Shopee Shop document for current transaction."""

        return frappe.get_doc("Shopee Shop", self.shopee_shop)
