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

    def get_stock_type_name(self):
        return self.STOCK_TYPES[self.stock_type]

    def get_stock_type(self):
        return str(self.stock_type)

    def get_current_stock(self):
        return self.current_stock

    def get_normal_stock(self):
        return self.normal_stock

    def get_reserved_stock(self):
        return self.reserved_stock
