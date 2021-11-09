import frappe
from unittest import mock, TestCase
from shopee_open_api.utils.client import get_shopless_client
from shopee_open_api.python_shopee.pyshopee2.client import Client


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
