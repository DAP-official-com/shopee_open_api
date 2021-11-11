import frappe, time, uuid
from unittest import mock, TestCase
from shopee_open_api.utils.client import get_shopless_client
from shopee_open_api.utils.datetime import datetime_string_from_unix
from .mock_data.orders import get_order_detail_response
from .mock_data.payments import get_escrow_detail_response
from .mock_data.products import get_item_base_info_response, get_model_list_response
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

        cls.ORDER_ID = uuid.uuid4().hex.upper()[0:6]
        order_detail_response = get_order_detail_response.copy()
        order_detail_response["response"]["order_list"][0]["order_sn"] = cls.ORDER_ID

        cls.order = Order(
            order_detail_response["response"]["order_list"][0],
            shop_id=cls.SHOP_ID,
        )

        cls.fake_item_id = uuid.uuid4().hex.upper()[:6]

        for order_item in cls.order.order_items:
            order_item.item_id = cls.fake_item_id

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

        order_ids = frappe.db.get_list(
            "Shopee Order",
            filters={
                "shopee_shop": cls.SHOP_ID,
            },
            pluck="name",
        )
        for order_id in order_ids:
            frappe.get_doc("Shopee Order", order_id).delete()

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

        order_ids = frappe.db.get_list(
            "Shopee Order",
            filters={
                "shopee_shop": self.SHOP_ID,
            },
            pluck="name",
        )
        for order_id in order_ids:
            frappe.get_doc("Shopee Order", order_id).delete()

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

    # def test_get_payment_escrow(self):
    #     self.assertIsInstance(self.order.get_payment_escrow(), PaymentEscrow)

    # def test_order_items_type(self):
    #     for item in self.order.order_items:
    #         self.assertIsInstance(item, OrderItem)

    # def test_update_or_insert(self):
    #     self.assertFalse(self.order.is_existing_in_database)

    #     self.assertEqual(
    #         frappe.db.count(
    #             "Shopee Order",
    #             filters={
    #                 "name": self.order.make_primary_key(),
    #             },
    #         ),
    #         0,
    #     )

    #     self.order.update_or_insert()

    #     self.assertTrue(self.order.is_existing_in_database)

    #     self.assertEqual(
    #         frappe.db.count(
    #             "Shopee Order",
    #             filters={
    #                 "name": self.order.make_primary_key(),
    #             },
    #         ),
    #         1,
    #     )

    #     self.order.update_or_insert()

    #     self.assertEqual(
    #         frappe.db.count(
    #             "Shopee Order",
    #             filters={
    #                 "name": self.order.make_primary_key(),
    #             },
    #         ),
    #         1,
    #     )

    def test_update_or_insert_with_items(self):
        with mock.patch(
            "shopee_open_api.shopee_models.base.ShopeeResponseBaseClass.client"
        ) as mock_client, mock.patch(
            "shopee_open_api.shopee_models.product.Product.client",
        ) as mock_product_client:

            mock_product_client.product.get_model_list.return_value = (
                get_model_list_response
            )
            get_item_base_info_response["response"]["item_list"][0][
                "item_id"
            ] = self.fake_item_id

            mock_client.product.get_item_base_info.return_value = (
                get_item_base_info_response
            )

            self.order.update_or_insert_with_items()
            self.assertTrue(
                frappe.get_all("Shopee Order", filters={"name": self.ORDER_ID})
            )

            self.assertEqual(
                frappe.db.count("Shopee Order", filters={"name": self.ORDER_ID}), 1
            )

            self.order.update_or_insert_with_items()
            self.assertEqual(
                frappe.db.count("Shopee Order", filters={"name": self.ORDER_ID}), 1
            )
