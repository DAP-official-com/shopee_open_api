from .base import ShopeeResponseBaseClass


class Stock(ShopeeResponseBaseClass):

    STOCK_TYPES = {
        1: "Shope Warehouse Stock",
        2: "Seller Warehouse Stock",
    }

    def to_json(self):
        response = self.__dict__.copy()
        response["stock_type_string"] = self.STOCK_TYPES[self.stock_type]
        response["product_id"] = self.product.get_product_id()
        response.pop("product", None)
        return response

    def is_existing_in_database(self):
        return False
