from .base import ShopeeResponseBaseClass
from .address import Address
import frappe


class Customer(ShopeeResponseBaseClass):
    """A class representing a shopee customer"""

    DOCTYPE = "Customer"

    DATA_FIELDS = (
        "customer_type",
        "customer_group",
        "customer_name",
        "territory",
        "username",
        "user_id",
        "shopee_user_id",
        "mobile_no",
    )

    @classmethod
    def from_shopee_customer(cls, *args, **kwargs):
        return cls(args, kwargs)

    def update_or_insert(self) -> None:
        if self.is_existing_in_database:
            customer = frappe.get_doc(self.DOCTYPE, self.get_primary_key())
        else:
            customer = frappe.get_doc(
                {
                    "doctype": self.DOCTYPE,
                }
            )

        for field in self.DATA_FIELDS:
            setattr(customer, field, getattr(self, field))

        customer.save()

    @property
    def is_existing_in_database(self) -> bool:
        return bool(
            frappe.db.exists(
                {
                    "doctype": self.DOCTYPE,
                    "shopee_user_id": self.shopee_user_id,
                    "customer_name": self.customer_name,
                }
            )
        )

    def get_primary_key(self) -> str:
        """Get name (primary key) field from existing customer, otherwise throw DoesNotExistError"""

        try:
            return frappe.db.get_list(
                self.DOCTYPE,
                filters={
                    "shopee_user_id": self.shopee_user_id,
                    "customer_name": self.customer_name,
                },
                pluck="name",
            )[0]
        except IndexError as e:
            raise frappe.exceptions.DoesNotExistError(
                f"Customer with Shopee user id {self.shopee_user_id} does not exist in the database"
            )

    @property
    def customer_detail(self) -> dict:
        return {attribute: getattr(self, attribute) for attribute in self.DATA_FIELDS}

    def add_address(self, address: Address) -> None:
        if self.has_address(address):
            address_link = frappe.get_doc(
                {
                    "doctype": "Dynamic Link",
                    "link_doctype": self.DOCTYPE,
                    "link_name": self.get_primary_key(),
                    "link_title": self.get_primary_key(),
                    "parent": address.get_primary_key(),
                    "parenttype": "Address",
                    "parentfield": "links",
                    "idx": 1,
                }
            )

            address_link.insert()

    def has_address(self, address: Address):
        return frappe.db.get_list(
            "Dynamic Link",
            filters={
                "link_doctype": self.DOCTYPE,
                "link_name": self.get_primary_key(),
                "parent": address.get_primary_key(),
                "parenttype": "Address",
                "parentfield": "links",
            },
        )
