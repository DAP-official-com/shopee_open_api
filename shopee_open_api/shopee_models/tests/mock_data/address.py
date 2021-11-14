import frappe
from shopee_open_api.shopee_models.customer import Customer
from shopee_open_api.shopee_models.tests.mock_data.customer import customer_data

address_data = {
    "city": "City name",
    "country": "Thailand",
    "state": "State name",
    "phone": "66888888888",
    "pincode": "10200",
    "address_type": "Postal",
    "full_address": "House number Area name City name State name Thailand 10200",
}
