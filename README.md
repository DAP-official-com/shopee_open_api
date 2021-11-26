## Shopee Open API Integration with ERPNext

This application contains submodule [DAP's Python-Shopee](https://github.com/DAP-official-com/python-shopee) to connect to Shopee Open Api. The submodule is forked from [original repository](https://github.com/JimCurryWang/python-shopee) and changes have been made to fix bugs and customize to our use.

## Installation

```shell
$ bench get-app shopee_open_api git@github.com:DAP-official-com/shopee_open_api.git
```

## Usage

_For further usages, such as creating a shopee order, products, etc., please read [this readme](/shopee_open_api/shopee_models/README.md)._

Make sure to have Shopee's App ID and App Key [(can be obtained here after logging in)](https://open.shopee.com/myconsole/management/app/detail?id=204203&bgIndex=0&name=DAP%20API) are set in the Shopee API Settings doctype before connecting to the client. Currently, authorization can be done from /app/branch.

```python
from shopee_open_api.utils.client import get_client_from_branch, get_client_from_shop


shop = frappe.get_doc("Shopee Shop", shop.name)
client = get_client_from_shop(shop)

## OR

branch = frappe.get_doc("Branch", branch.name)
client = get_client_from_branch(branch)


## get item list
item_list = client.product.get_item_list(
    item_status="NORMAL", offset=0, page_size=100
)["response"]["item"]
print(item_list)

## get all categories
categories = client.product.get_category(language="TH")["response"]
print(categories)

# shop authorize url
authorize_url = client.shop_authorization(redirect_url=client.redirect_url)
print(authorize_url)
```

## _6_ main parts of implementation

#### 1. Shop Management Module : [Shop](https://open.shopee.com/documents?module=6&type=1&id=410) / [ShopCategory](https://open.shopee.com/documents?module=7&type=1&id=404)

#### 2. Orders Management Module : [Orders](https://open.shopee.com/documents?module=4&type=1&id=394)

#### 3. Logistics Management Module : [Logistics](https://open.shopee.com/documents?module=3&type=1&id=384)

#### 4. Products Management Module : [Item](https://open.shopee.com/documents?module=2&type=1&id=365) / [Image](https://open.shopee.com/documents?module=65&type=1&id=412) / [Discount](https://open.shopee.com/documents?module=1&type=1&id=357)

#### 5. RMA Management Module : [Returns](https://open.shopee.com/documents?module=5&type=1&id=401)

#### 6. Collection Management Module: [toppicks](https://open.shopee.com/documents?module=67&type=1&id=435)

## Quick Start

#### Import pyshopee & get products under this shop

```python
from shopee_open_api.utils.client import get_client_from_branch

shop = frappe.get_doc("Shopee Shop", shop_id)
client = get_client_from_shop(shop)

## get item list
item_list = client.product.get_item_list(
    item_status="NORMAL", offset=0, page_size=100
)["response"]["item"]
print(item_list)

## get all categories
categories = client.product.get_category(language="TH")["response"]
print(categories)

```

### <span style="font-color:red">The code below is from original repository and has not been tested.</span>

#### Get order list

```python
# get_order_list
resp = client.order.get_order_list(create_time_from = 1512117303, create_time_to=1512635703)
print(resp)
```

#### Get order detail

```python
'''
ordersn_list , type: String[]
The set of order IDs. You can specify, at most, 100 OrderIDs in this call.
'''
# get_order_detail
ordersn_list = [ '1712071633982A7','1712071632981JW','171207163097YCJ']
resp = client.order.get_order_detail(ordersn_list = ordersn_list )
print(resp)
```

#### Get order escrow detail

```python
'''
ordersn , type:String []
Shopee's unique identifier for an order.
'''
# get_order_escrow_detail
ordersn = '1712071633982A7'
resp = client.order.get_order_escrow_detail(ordersn = ordersn)
print(resp)
```

## Advance Details for others functions

```python
# usage
client.[type].[function name]

[type]
  - Shop
  - ShopCategory
  - Orders
  - Logistics
  - Item
  - Image
  - Discount
  - Returns
```

## Advance parameters you must want to know

### Timeout

You can find the source code in client.py, and pyshopee have a timeout params in there.
Hence, every execute funtion can add an extra timeout setting, depending on your choice.

```python

def execute(self, uri, method, body=None, files=None):
    """defalut timeout value will be 10 seconds"""
    # parameter = self._make_default_parameter()
    if body.get("timeout"):
        timeout = body.get("timeout")
        body.pop("timeout")
    else:
        timeout = 10

    # if body is not None:
    # parameter.update(body)

    req = self._build_request(uri, method, body, files)

    if self.test_env:
        print(f"req.params: {req.params}")
        print(f"req.url: {req.url}")

    prepped = req.prepare()

    s = Session()
    resp = s.send(prepped, timeout=timeout)
    resp = self._build_response(resp)
    return resp
```

For example, we can set the timeout as 20 seconds in the execute requests(default value is 10s).

```python
ordersn = '1712071633982A7'
resp = client.order.get_order_escrow_detail(ordersn = ordersn, timeout=20)
print(resp)

```

## Note

_Original Package Source code_  
 https://github.com/JimCurryWang/pyshopee

_Shopee Open API Documentation_  
 https://open.shopee.com/documents?module=87&type=2&id=64&version=2

## Run Tests

```console
## Create a new site for testing.
bench new-site {sitename} --install-app shopee_open_api

## Set config to allow testing
bench --site {sitename} set-config allow_tests true

## Run tests
bench --site {sitename} run-tests --app shopee_open_api --skip-test-records
```
