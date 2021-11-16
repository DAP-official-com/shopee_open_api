import frappe
from unittest import mock, TestCase
from shopee_open_api.utils.client import get_shopless_client
from shopee_open_api.python_shopee.pyshopee2.client import Client
from shopee_open_api.python_shopee.pyshopee2.exceptions import OnlyGetMethodAllowedError


class ClientTest(TestCase):
    def test_get_shopless_client(self):
        client = get_shopless_client()
        self.assertIsInstance(client, Client)

    def test_currect_auth_url_redirect(self):

        client = get_shopless_client()
        auth_url = client.shop_authorization(redirect_url=client.redirect_url)
        site_host_url = frappe.utils.get_url()

        auth_redirect_url = (
            site_host_url + "/api/method/shopee_open_api.auth.authorize_callback"
        )

        self.assertIn(auth_redirect_url, auth_url)

    def test_only_allow_get(self):

        frappe.db.set_value(
            "Shopee API Settings",
            "Shopee API Settings",
            "prevent_making_changes_on_shopee_portal",
            1,
        )

        client = get_shopless_client()

        with self.assertRaises(OnlyGetMethodAllowedError):
            client.product.reply_comment()
