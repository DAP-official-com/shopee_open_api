from .base import ShopeeResponseBaseClass


class Model(ShopeeResponseBaseClass):
    def __str__(self):
        return self.name
