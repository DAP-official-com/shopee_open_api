import json
from shopee_open_api.utils.client import get_client_from_shop_id


class ShopeeResponseBaseClass(json.JSONEncoder):
    """Shopee model base class for all shopee models"""

    def __init__(self, *initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
            for key, value in kwargs.items():
                setattr(self, key, value)

    @property
    def client(self):

        if not hasattr(self, "shop_id"):
            raise NotImplementedError("Property shop_id is required to get the client")

        return get_client_from_shop_id(self.shop_id)

    def __str__(self):
        return f"{self.__class__.__name__}"

    def to_json(self):
        return json.loads(
            json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        )
