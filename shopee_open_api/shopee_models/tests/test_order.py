import frappe, time, uuid
from unittest import mock, TestCase
from shopee_open_api.utils.client import get_shopless_client
from shopee_open_api.utils.datetime import datetime_string_from_unix
from .mock_data.orders import get_order_detail_response
from .mock_data.payments import get_escrow_detail_response
from .mock_data.products import product_base_info
from shopee_open_api.shopee_models.order import Order
from shopee_open_api.shopee_models.payment_escrow import PaymentEscrow
from shopee_open_api.shopee_models.order_item import OrderItem


class ShopeeProductTest(TestCase):
    """Test model representing objects on shopee api"""

    @classmethod
    def setUpClass(cls):
        cls.patcher = mock.patch("shopee_open_api.shopee_models.order.Order.client")
        cls.mock_client = cls.patcher.start()
        cls.mock_client.payment.get_escrow_detail.return_value = (
            get_escrow_detail_response
        )

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

        cls.order = Order(
            get_order_detail_response["response"]["order_list"][0], shop_id=cls.SHOP_ID
        )

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

        product_ids = frappe.db.get_list(
            "Shopee Product",
            filters={
                "shopee_shop": cls.SHOP_ID,
            },
            pluck="name",
        )
        for product_id in product_ids:
            frappe.get_doc("Shopee Product", product_id).delete()

        order_ids = frappe.db.get_list(
            "Shopee Order",
            filters={
                "shopee_shop": cls.SHOP_ID,
            },
            pluck="name",
        )
        for order_id in order_ids:
            frappe.get_doc("Shopee Order", order_id).delete()

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

        self.order.payment_escrow = None

    def test_get_payment_escrow(self):
        self.assertIsInstance(self.order.get_payment_escrow(), PaymentEscrow)

    def test_order_items_type(self):
        for item in self.order.order_items:
            self.assertIsInstance(item, OrderItem)

    def test_update_or_insert(self):
        self.assertFalse(self.order.is_existing_in_database)

        self.assertEqual(
            frappe.db.count(
                "Shopee Order",
                filters={
                    "name": self.order.make_primary_key(),
                },
            ),
            0,
        )

        self.order.update_or_insert()

        self.assertTrue(self.order.is_existing_in_database)

        self.assertEqual(
            frappe.db.count(
                "Shopee Order",
                filters={
                    "name": self.order.make_primary_key(),
                },
            ),
            1,
        )

        self.order.update_or_insert()

        self.assertEqual(
            frappe.db.count(
                "Shopee Order",
                filters={
                    "name": self.order.make_primary_key(),
                },
            ),
            1,
        )

    def test_update_or_insert_with_items(self):
        self.order.update_or_insert_with_items()
