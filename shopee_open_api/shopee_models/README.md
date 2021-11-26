# Shopee API Models

Classes in this directory represent each object in Shopee API, not the doctype itself. For example, the Order class represents a single order, and a Product class represents one product as returned from Shopee API.

## How to use

First, get the client for a shop. There are [other ways](https://git.arterypartner.com/artery/ap-application/shopee_open_api/-/blob/develop/shopee_open_api/utils/client.py) to get a client as well.

```python
import frappe
from shopee_open_api.utils.client import get_client_from_shop_id, get_client_from_shop

shop_id = 28211
client = get_client_from_shop_id(shop_id)

shop = frappe.get_last_doc("Shopee Shop")
client  = get_client_from_shop(shop)
```

## How to use

### Order class

An order class contains a list of OrderItem objects, a PaymentEscrow object, and a list of Product objects.

```python
from shopee_open_api.shopee_models.order import Order

order_detail_response = client.order.get_order_detail(
                            order_sn_list=order_sn,
                            response_optional_fields="buyer_user_id,buyer_username,estimated_shipping_fee,recipient_address,actual_shipping_fee,goods_to_declare,note,note_update_time,item_list,pay_time,dropshipper,credit_card_number,dropshipper_phone,split_up,buyer_cancel_reason,cancel_by,cancel_reason,actual_shipping_fee_confirmed,buyer_cpf_id,fulfillment_flag,pickup_done_time,package_list,shipping_carrier,payment_method,total_amount,buyer_username,invoice_data,checkout_shipping_carrier,reverse_shipping_fee",
                        )

order_list = order_detail_response["response"]["order_list"]
orders = [Order(order_details, shop_id=shop_id) for order_details in order_list]

# Save this order to the database
orders[0].update_or_insert_with_items(ignore_permissions=False)

# Get the order items
orders[0].order_items

# Get the products in the order
orders[0].get_shopee_products() # Calls Shopee API to retrieve the products' data

```

### Product class

A product class represents a single product on Shopee. There are singular product, which is a product itself, and product with variants, which contains models of that certain product.

```python
from shopee_open_api.shopee_models.product import Product

get_item_list_response = client.product.get_item_list(
                            offset=offset,
                            item_status=item_status,
                            page_size=50,
                        )

item_ids = get_item_list_response["response"]["item"]

product_details_response = client.product.get_item_base_info(
                                item_id_list=",".join([str(item["item_id"]) for item in item_ids])
                            )

product_details = product_details_response["response"]["item_list"]

# Instantiate all the products.
products = [
                Product(product_detail, shop_id=shop_id) for product_detail in product_details
            ]

singular_products = [product for product in products if not product.has_model]
multi_variants_products = [product for product in products if product.has_model]

# Update existing or insert new product.
singular_products[0].update_or_insert(ignore_permissions=False)
```

Please note that a singular product has all the data neccessary by calling get_item_base_info, but a product with varaints needs to send another requests by calling get_model_list, which accepts only one product at a time. Therefore, updating or inserting a list of singular products are much faster than products with variants

```python
# This is fast.
[product.update_or_insert() for product in singular_products]

# This is slow, because each product needs to call an additional api to retrieve model details.
[product.update_or_insert() for product in multi_variants_products]
```
