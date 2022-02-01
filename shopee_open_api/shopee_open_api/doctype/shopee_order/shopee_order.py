# Copyright (c) 2021, Dap Official and contributors
# For license information, please see license.txt

import frappe

from erpnext.selling.doctype.sales_order import sales_order
from erpnext.accounts.doctype.sales_invoice import sales_invoice
from erpnext.stock.doctype.delivery_note import delivery_note

from frappe.model.document import Document
from shopee_open_api.shopee_models.address import Address
from shopee_open_api.shopee_models.customer import Customer
from shopee_open_api.exceptions import ProductHasNoItemError, ItemHasNoPriceError
from shopee_open_api.shopee_open_api.doctype.shopee_order_item.shopee_order_item import (
    ShopeeOrderItem,
)
from typing import List, Optional


class ShopeeOrder(Document):

    STATUSES_TO_CREATE_SALES_INVOICE = [
        "COMPLETED",
    ]

    STATUSES_TO_CREATE_DELIVERY_NOTE = STATUSES_TO_CREATE_SALES_INVOICE.copy() + [
        "SHIPPED",
        "TO_CONFIRM_RECEIVE",
    ]

    def get_shopee_shop_instance(self):
        """Get an object of Shopee Shop doctype this order belongs to."""

        return frappe.get_doc("Shopee Shop", self.shopee_shop)

    @property
    def customer_detail(self) -> dict:
        # Get the data for Customer Doctype

        customer = {}

        customer["customer_type"] = "Individual"
        customer["customer_group"] = "Shopee"
        customer["customer_name"] = self.recipient_name
        customer["territory"] = frappe.db.get_default("Country")
        customer["username"] = self.buyer_username
        customer["user_id"] = self.buyer_user_id
        customer["shopee_user_id"] = self.buyer_user_id
        customer["mobile_no"] = self.recipient_phone
        customer["default_price_list"] = (
            self.get_shopee_shop_instance().get_price_list().name
        )

        return customer

    def get_customer_instance(self) -> Customer:
        """Get an instance of a customer (shopee customer, not erpnext customer)"""

        return Customer.from_shopee_customer(**self.customer_detail)

    @property
    def address_detail(self) -> dict:
        """Get the data for Address doctype"""

        address = {}

        address["city"] = self.recipient_city
        address["country"] = frappe.db.get_default("Country")
        address["state"] = self.recipient_state
        address["phone"] = self.recipient_phone
        address["pincode"] = self.recipient_zipcode
        address["address_type"] = "Postal"
        address["full_address"] = self.recipient_full_address

        address["customer"] = self.get_customer_instance()

        return address

    def get_address_instance(self) -> Address:
        """Get an instance of an address (shopee address, not erpnext address)"""

        return Address.from_shopee_address(**self.address_detail)

    def run_order_automation(self, ignore_permissions=False):
        """
        Perform sales order automation process.

        - Create a sales order draft
        - Submit a sales order
        - Create a delery note
        - Create a sales invoice
        """

        shop = self.get_shopee_shop_instance()

        if shop.is_set_to_create_draft_sales_order:
            new_order = self.create_sales_order(ignore_permissions=ignore_permissions)
            frappe.db.commit()

        if (
            shop.is_set_to_submit_sales_order
            and new_order is not None
            and new_order.docstatus == 0
        ):
            self.submit_sales_order(ignore_permissions=ignore_permissions)
            frappe.db.commit()

        if self.should_create_delivery_note:
            self.create_delivery_note()
            frappe.db.commit()

        if self.should_submit_delivery_note:
            self.submit_delivery_note()
            frappe.db.commit()

        if self.should_create_sales_invoice:
            self.create_sales_invoice()
            frappe.db.commit()

        if self.should_submit_sales_invoice:
            self.submit_sales_invoice()
            frappe.db.commit()

    def create_sales_order(self, ignore_permissions=False) -> sales_order.SalesOrder:
        """Create Sales Order document from Shopee Order"""

        if self.sales_order:
            return frappe.get_doc("Sales Order", self.sales_order)

        self.create_sales_order_validate()

        self.pre_create_sales_order(ignore_permissions=ignore_permissions)

        shop = self.get_shopee_shop_instance()

        new_sales_order = frappe.new_doc("Sales Order")
        new_sales_order.customer = self.get_customer_instance().get_primary_key()
        new_sales_order.order_type = "Sales"
        new_sales_order.transaction_date = self.create_time
        new_sales_order.delivery_date = self.create_time
        new_sales_order.customer_address = self.get_address_instance().get_primary_key()
        new_sales_order.set_warehouse = shop.get_warehouse().name
        new_sales_order.selling_price_list = shop.get_price_list().name

        for order_item in self.order_items:
            shopee_product = order_item.get_shopee_product()
            item = shopee_product.get_item()

            sales_order_item = new_sales_order.append("items", {})
            sales_order_item.item_code = item.name
            sales_order_item.qty = order_item.qty
            sales_order_item.rate = (
                order_item.get_shopee_product().get_item_price().price_list_rate
            )
            sales_order_item.uom = order_item.get_shopee_product().get_item_price().uom

        new_sales_order.insert(ignore_permissions=ignore_permissions)

        self.sales_order = new_sales_order.name

        self.save(ignore_permissions=ignore_permissions)

        return new_sales_order

    def submit_sales_order(self, ignore_permissions=False):
        if self.sales_order is None:
            return

        sales_order_document = frappe.get_doc("Sales Order", self.sales_order)

        if sales_order_document.docstatus == 1:
            return sales_order_document

        sales_order_document.submit()
        return sales_order_document

    @property
    def order_items(self) -> List[ShopeeOrderItem]:
        """Get a list of Shopee Order Items belonging to this order."""

        return self.get("shopee_order_items")

    def create_sales_order_validate(self):
        """Perform validation before creating a new sales order"""

        self.shopee_order_items_validate()

    def shopee_order_items_validate(self):
        """Check that all Shopee Order Items are matched with erpnext Item"""

        for order_item in self.order_items:
            if order_item.get_shopee_product().item is None:
                frappe.throw(
                    msg=f"Shopee product {order_item.get_shopee_product()} has not been matched with erpnext item",
                    exc=ProductHasNoItemError,
                )

            if not order_item.get_shopee_product().has_item_price():
                frappe.throw(
                    msg=f"Could not find an Item Price belonging to the product {order_item.get_shopee_product().name}",
                    exc=ItemHasNoPriceError,
                )

    def pre_create_sales_order(self, ignore_permissions=False):
        """Perform actions before creating a sales order, e.g. creating a customer and address, if none exists"""

        if not self.customer:
            self.create_customer_document(ignore_permissions=ignore_permissions)
            self.create_address_document(ignore_permissions=ignore_permissions)

            customer = self.get_customer_instance()
            address = self.get_address_instance()
            customer.add_address(address)

    def create_customer_document(self, ignore_permissions=False):
        """Create a new customer or update current customer document for the order's buyer"""

        self.get_customer_instance().update_or_insert(
            ignore_permissions=ignore_permissions
        )

    def create_address_document(self, ignore_permissions=False):
        """Create a new address or update current address document for the order's buyer"""

        self.get_address_instance().update_or_insert(
            ignore_permissions=ignore_permissions
        )

    def save(self, *args, **kwargs):
        self.create_cancel_reason()
        self.create_payment_method()
        super().save(*args, **kwargs)

    def before_save(self):
        """Controller: Update or insert a Customer document along with the Address"""

        self.create_customer_document(ignore_permissions=True)
        self.create_address_document(ignore_permissions=True)

        customer = self.get_customer_instance()
        address = self.get_address_instance()

        customer.add_address(address, ignore_permissions=True)
        self.customer = customer.get_primary_key()
        self.address = address.get_primary_key()

    def before_insert(self):
        """Create linked documents if neccessary"""

        self.create_cancel_reason()
        self.create_payment_method()

    def create_cancel_reason(self):
        """Create cancel reason if not exists in the database."""

        if not self.cancel_reason:
            return

        if frappe.db.exists("Shopee Cancel Reason", self.cancel_reason):
            return

        cancel_reason = frappe.new_doc("Shopee Cancel Reason")
        cancel_reason.cancel_status = self.cancel_reason
        cancel_reason.insert(ignore_permissions=True)

    def create_payment_method(self):
        """Create payment method if not exists in the database."""

        if not self.payment_method:
            return

        if frappe.db.exists("Shopee Payment Method", self.payment_method):
            return

        payment_method = frappe.new_doc("Shopee Payment Method")
        payment_method.payment_type = self.payment_method
        payment_method.insert(ignore_permissions=True)

    @property
    def should_create_delivery_note(self) -> bool:

        if self.delivery_note is not None:
            return False

        shop = self.get_shopee_shop_instance()

        if (
            shop.is_set_to_create_delivery_note
            and self.order_status.upper() in self.STATUSES_TO_CREATE_DELIVERY_NOTE
        ):
            return True

        return False

    def create_delivery_note(
        self, ignore_permissions=False
    ) -> delivery_note.DeliveryNote:
        """Create delivery note from this order."""

        if self.sales_order is None:
            return None

        if self.delivery_note:
            return frappe.get_doc("Delivery Note", self.delivery_note)

        sales_order_document = self.get_sales_order_document()
        if sales_order_document.docstatus == 0:
            sales_order_document.submit()

        new_delivery_note = sales_order.make_delivery_note(source_name=self.sales_order)
        new_delivery_note.insert(ignore_permissions=ignore_permissions)

        self.delivery_note = new_delivery_note.name
        self.save(ignore_permissions=ignore_permissions)

        return new_delivery_note

    @property
    def should_submit_delivery_note(self):

        if self.delivery_note is None:
            return False

        shop = self.get_shopee_shop_instance()
        if (
            shop.is_set_to_create_delivery_note
            and self.order_status.upper() not in self.STATUSES_TO_CREATE_DELIVERY_NOTE
        ):
            return False

        delivery_note_document = frappe.get_doc("Delivery Note", self.delivery_note)
        if delivery_note_document.docstatus == 1:
            return False

        return True

    def submit_delivery_note(self, ignore_permissions=False):

        if self.delivery_note is None:
            return None

        delivery_note = frappe.get_doc("Delivery Note", self.delivery_note)

        if delivery_note.docstatus == 1:
            return delivery_note

        delivery_note.submit()

        return delivery_note

    @property
    def should_create_sales_invoice(self) -> bool:

        if self.sales_invoice is not None:
            return False

        shop = self.get_shopee_shop_instance()

        if (
            shop.is_set_to_create_sales_invoice
            and self.order_status.upper() in self.STATUSES_TO_CREATE_SALES_INVOICE
        ):
            return True

        return False

    def create_sales_invoice(
        self, ignore_permissions=False
    ) -> Optional[sales_invoice.SalesInvoice]:

        if self.sales_order is None or self.delivery_note is None:
            return None

        if self.sales_invoice:
            return frappe.get_doc("Sales Invoice", self.sales_invoice)

        delivery_note_document = self.get_delivery_note_document()
        if delivery_note_document.docstatus == 0:
            delivery_note_document.submit()

        new_sales_invoice = delivery_note.make_sales_invoice(
            source_name=self.delivery_note
        )
        new_sales_invoice.debit_to = (
            self.get_shopee_shop_instance().get_receivable_account().name
        )
        new_sales_invoice.insert(ignore_permissions=ignore_permissions)

        self.sales_invoice = new_sales_invoice.name
        self.save(ignore_permissions=ignore_permissions)

        return new_sales_invoice

    @property
    def should_submit_sales_invoice(self) -> bool:
        if self.sales_invoice is None:
            return False

        shop = self.get_shopee_shop_instance()
        if (
            shop.is_set_to_create_sales_invoice
            and self.order_status.upper() not in self.STATUSES_TO_CREATE_SALES_INVOICE
        ):
            return False

        sales_invoice_doc = frappe.get_doc("Sales Invoice", self.sales_invoice)
        if sales_invoice_doc.docstatus == 1:
            return False

        return True

    def submit_sales_invoice(self) -> sales_invoice.SalesInvoice:
        new_sales_invoice = frappe.get_doc("Sales Invoice", self.sales_invoice)

        if new_sales_invoice.docstatus == 0:
            new_sales_invoice.submit()

        return new_sales_invoice

    def get_delivery_note_document(self):
        if self.delivery_note is None:
            return None
        return frappe.get_doc("Delivery Note", self.delivery_note)

    def get_sales_order_document(self):
        if self.sales_order is None:
            return None
        return frappe.get_doc("Sales Order", self.sales_order)
