from .base import ShopeeResponseBaseClass
from .address import Address
import frappe


class Customer(ShopeeResponseBaseClass):
    """
    A class representing a shopee customer from Shopee API's response.
    The class is interacting with ERPNext's Customer doctype, not the same as erpnext Customer doctype itself.
    """

    DOCTYPE = "Customer"

    ## The data fields to be used for creating and editing the Customer doctype.
    DATA_FIELDS = (
        "customer_type",
        "customer_group",
        "customer_name",
        "territory",
        "username",
        "user_id",
        "shopee_user_id",
        "default_price_list",
        # "mobile_no", # ignore mobile number for now. when creating a new customer, if mobile number is provided, a Contact is also created, but we cannot override the permission
    )

    @classmethod
    def from_shopee_customer(cls, *args, **kwargs):
        """Instantiate the class with a shopee customer"""
        return cls(args, kwargs)

    def update_or_insert(self, ignore_permissions=False) -> None:
        """Update or insert ERPNext's Customer doctype into the database. Take the fields from DATA_FIELDS attribute"""

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

        customer.save(ignore_permissions=ignore_permissions)

    @property
    def is_existing_in_database(self) -> bool:
        """Check if the current shopee customer exists as a Customer doctype in the database"""

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
            return frappe.db.get_all(
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
        """Get customer details based on the DATA_FIELDS attribute, which can be used to update or insert new customer"""

        return {attribute: getattr(self, attribute) for attribute in self.DATA_FIELDS}

    def add_address(self, address: Address, ignore_permissions=False) -> None:
        """Insert a new ERPNext's address document from the address retrieved from Shopee API"""

        if not self.has_address(address):
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

            address_link.insert(ignore_permissions=ignore_permissions)

    def has_address(self, address: Address) -> bool:
        """Check if the user has the address from Shopee API"""

        return bool(
            frappe.db.get_list(
                "Dynamic Link",
                filters={
                    "link_doctype": self.DOCTYPE,
                    "link_name": self.get_primary_key(),
                    "parent": address.get_primary_key(),
                    "parenttype": "Address",
                    "parentfield": "links",
                },
            )
        )
