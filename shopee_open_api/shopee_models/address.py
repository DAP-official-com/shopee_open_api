from .base import ShopeeResponseBaseClass
import frappe


class Address(ShopeeResponseBaseClass):
    """A class representing a shopee customer"""

    DOCTYPE = "Address"

    DATA_FIELDS = (
        "city",
        "country",
        "state",
        "phone",
        "pincode",
        "address_line1",
        "address_title",
        "address_type",
    )

    def update_or_insert(self) -> None:
        if self.is_existing_in_database:
            address = frappe.get_doc(self.DOCTYPE, self.get_primary_key())
        else:
            address = frappe.get_doc({"doctype": self.DOCTYPE})

        for field in self.DATA_FIELDS:
            setattr(address, field, getattr(self, field))

        address.save()

    @classmethod
    def from_shopee_address(cls, *args, **kwargs):

        if "customer" not in kwargs:
            raise ValueError("Shopee customer object is required")

        address = cls(args, kwargs)

        address.address_line1 = " ".join(
            (
                address.full_address.replace(address.city, "")
                .replace(address.country, "")
                .replace(address.pincode, "")
                .replace(address.state, "")
            ).split()
        )

        address.address_title = address.customer.customer_name

        return address

    @property
    def address_detail(self) -> dict:
        return {attribute: getattr(self, attribute) for attribute in self.DATA_FIELDS}

    @property
    def is_existing_in_database(self) -> bool:
        return bool(frappe.db.exists({"doctype": "Address", **self.address_detail}))

    def get_primary_key(self) -> str:
        try:
            return frappe.db.get_list(
                self.DOCTYPE,
                filters=self.address_detail,
                pluck="name",
            )[0]
        except IndexError as e:
            raise frappe.exceptions.DoesNotExistError(
                f"The address {self.address_line1} does not exist in the database"
            )
