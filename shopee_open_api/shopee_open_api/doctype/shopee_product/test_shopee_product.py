# Copyright (c) 2021, Dap Official and Contributors
# See license.txt

# import frappe
import frappe, time, uuid
from unittest import mock, TestCase
from shopee_open_api.utils.client import get_shopless_client
from shopee_open_api.utils.datetime import datetime_string_from_unix
from shopee_open_api.shopee_models.tests.mock_data.products import (
    product_base_info,
    get_model_list_response,
)
from shopee_open_api.shopee_models.product import Product
from frappe.exceptions import DuplicateEntryError, DoesNotExistError


class TestShopeeProduct(TestCase):
    @classmethod
    def setUpClass(cls):

        cls.SHOP_ID = uuid.uuid4().hex.upper()[0:6]

        cls.client = get_shopless_client()

        token = frappe.get_doc(
            doctype="Shopee Token",
            shop_id=cls.SHOP_ID,
            access_token="ACCESS TOKEN",
            refresh_token="REFRESH TOKEN",
            token_expiration_unix=int(time.time()),
            authorization_time=datetime_string_from_unix(time.time()),
            expiration_time=datetime_string_from_unix(time.time() + 60000),
        )
        token.insert()
        cls.token = token

        shop = frappe.get_doc(
            doctype="Shopee Shop",
            name=cls.SHOP_ID,
            shop_id=cls.SHOP_ID,
            shop_name="TEST SHOP",
            token=cls.SHOP_ID,
        )
        shop.insert()
        cls.shop = shop

        for product in product_base_info:
            """Set new product id for each item so that they don't clash with real products in the database"""
            product["item_id"] = uuid.uuid4().hex.upper()[0:16]

        cls.products = [
            Product(product, shop_id=cls.SHOP_ID) for product in product_base_info
        ]

        shopee_product = [product for product in cls.products if not product.has_model][
            0
        ]
        shopee_product.update_or_insert()
        cls.product = frappe.get_doc(
            "Shopee Product", shopee_product.make_primary_key()
        )

    @classmethod
    def tearDownClass(cls):

        product_ids = frappe.db.get_list(
            "Shopee Product",
            filters={
                "shopee_shop": cls.SHOP_ID,
            },
            pluck="name",
        )
        for product_id in product_ids:
            frappe.get_doc("Shopee Product", product_id).delete()

        cls.shop.delete()
        cls.token.delete()

    def tearDown(self):
        frappe.set_user("Administrator")
        product_ids = frappe.db.get_list(
            "Shopee Product",
            filters={
                "shopee_shop": self.SHOP_ID,
            },
            pluck="name",
        )
        for product_id in product_ids:
            frappe.get_doc("Shopee Product", product_id).delete()

        try:
            self.product.get_item().delete()
        except DoesNotExistError as e:
            pass

    def test_create_new_item_from_product(self):

        new_item = self.product.create_new_item_from_product()

        self.assertTrue(frappe.db.exists("Item", new_item.name))

        with self.assertRaises(DuplicateEntryError):
            self.product.create_new_item_from_product()

    def test_get_item(self):
        with self.assertRaises(DoesNotExistError):
            self.product.get_item()

        self.product.create_new_item_from_product()

        self.assertEqual(
            self.product.get_item().name, self.product.get_item_primary_key()
        )

    def test_create_new_item_and_add_to_product(self):
        self.assertIsNone(self.product.item)

        self.product.create_new_item_and_add_to_product()

        self.assertEqual(self.product.item, self.product.get_item_primary_key())
