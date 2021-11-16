from unittest import TestCase, mock
from shopee_open_api.shopee_models.customer import Customer, Address
from .mock_data.customer import customer_data
from .mock_data.address import address_data
import frappe


class TestAddress(TestCase):
    def setUp(self):
        self.customer = Customer.from_shopee_customer(**customer_data)
        self.address = Address.from_shopee_address(
            **address_data, customer=self.customer
        )

    def tearDown(self):
        if self.address.is_existing_in_database:
            frappe.get_doc("Address", self.address.get_primary_key()).delete()

    def test_is_existing_in_database(self):
        self.assertFalse(self.address.is_existing_in_database)

        self.address.update_or_insert()
        self.assertTrue(self.address.is_existing_in_database)

    def test_get_primary_key(self):

        with self.assertRaises(frappe.exceptions.DoesNotExistError):
            self.address.get_primary_key()

        self.address.update_or_insert()
        self.assertIsNotNone(self.address.get_primary_key())

    def test_update_or_insert(self):

        self.assertEqual(frappe.db.count("Address", self.address.address_detail), 0)

        self.address.update_or_insert()
        self.assertEqual(frappe.db.count("Address", self.address.address_detail), 1)

        self.address.update_or_insert()
        self.assertEqual(frappe.db.count("Address", self.address.address_detail), 1)

    def test_from_shopee_address(self):
        with self.assertRaises(ValueError):
            address = Address.from_shopee_address(**address_data)

        address = Address.from_shopee_address(**address_data, customer=self.customer)

        self.assertIsNotNone(address.address_line1)
        self.assertIsNotNone(address.address_title)
