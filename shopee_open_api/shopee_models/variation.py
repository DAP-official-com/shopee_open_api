from .base import ShopeeResponseBaseClass


class Variation(ShopeeResponseBaseClass):
    def __str__(self):
        return self.name
