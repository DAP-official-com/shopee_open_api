from unittest import TestCase, mock
from shopee_open_api.shopee_models.customer import Customer, Address
from .mock_data.customer import customer_data
from .mock_data.address import address_data
import frappe


class TestCustomer(TestCase):
    def setUp(self):
        self.customer = Customer(customer_data)
        self.address = Address.from_shopee_address(
            **address_data, customer=self.customer
        )
        self.address.update_or_insert()

    def tearDown(self):
        if self.customer.is_existing_in_database:
            frappe.get_doc("Customer", self.customer.get_primary_key()).delete()

    def test_creating_customer_from_shopee_customer(self):
        customer = Customer.from_shopee_customer(**customer_data)
        self.assertEqual(self.customer.to_json(), customer.to_json())

    def test_is_existing_in_database(self):
        self.assertFalse(self.customer.is_existing_in_database)

        self.customer.update_or_insert()
        self.assertTrue(self.customer.is_existing_in_database)

    def test_has_address(self):
        self.customer.update_or_insert()

        self.assertFalse(self.customer.has_address(self.address))

        self.customer.add_address(self.address)

        self.assertTrue(self.customer.has_address(self.address))
