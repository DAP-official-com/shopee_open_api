# Copyright (c) 2021, Dap Official and Contributors
# See license.txt

import unittest, uuid, time, frappe, json
from unittest import mock
from shopee_open_api.utils.client import get_shopless_client
from shopee_open_api.utils.datetime import datetime_string_from_unix
from shopee_open_api.shopee_models.tests.mock_data.orders import (
    get_order_detail_response,
)
from shopee_open_api.shopee_models.tests.mock_data.payments import (
    get_escrow_detail_response,
)
from shopee_open_api.shopee_models.tests.mock_data.products import (
    get_item_base_info_response,
    get_model_list_response,
)
from shopee_open_api.shopee_models.order import Order
from shopee_open_api.shopee_open_api.doctype.shopee_shop.shopee_shop import ShopeeShop
from frappe.exceptions import ValidationError


class TestShopeeOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patcher = mock.patch("shopee_open_api.shopee_models.order.Order.client")
        cls.mock_client = cls.patcher.start()
        cls.mock_client.payment.get_escrow_detail.return_value = (
            get_escrow_detail_response
        )

        cls.product_client_patcher = mock.patch(
            "shopee_open_api.shopee_models.product.Product.client"
        )
        cls.mock_product_client = cls.product_client_patcher.start()
        cls.mock_product_client.product.get_model_list.return_value = (
            get_model_list_response
        )

        cls.base_client_patcher = mock.patch(
            "shopee_open_api.shopee_models.base.ShopeeResponseBaseClass.client"
        )

        cls.fake_item_id = uuid.uuid4().hex.upper()[:6]

        get_item_base_info_response["response"]["item_list"][0][
            "item_id"
        ] = cls.fake_item_id

        cls.mock_base_client = cls.base_client_patcher.start()

        cls.mock_base_client.product.get_item_base_info.return_value = (
            get_item_base_info_response
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

        order = Order(
            order_detail_response["response"]["order_list"][0],
            shop_id=cls.SHOP_ID,
        )

        for order_item in order.order_items:
            order_item.item_id = cls.fake_item_id

        cls.order = order.update_or_insert_with_items()

    @classmethod
    def tearDownClass(cls):
        mock.patch.stopall()

        cls.order.delete()

        if cls.order.sales_order:
            frappe.get_doc("Sales Order", cls.order.sales_order).delete()

        product_ids = frappe.db.get_all(
            "Shopee Product", filters={"shopee_shop": cls.shop.name}, pluck="name"
        )

        for product_id in product_ids:
            frappe.get_doc("Shopee Product", product_id).delete()

        cls.shop.delete()
        cls.token.delete()

    def test_get_shopee_shop_instance(self):
        self.assertIsInstance(self.order.get_shopee_shop_instance(), ShopeeShop)

    def test_create_sales_order(self):
        with self.assertRaises(ValidationError):
            self.order.create_sales_order()

        for order_item in self.order.order_items:
            order_item.get_shopee_product().create_new_item_and_add_to_product()

        sales_order = self.order.create_sales_order()

        self.assertIsNotNone(self.order.sales_order)

        self.assertEqual(len(sales_order.get("items")), len(self.order.order_items))
