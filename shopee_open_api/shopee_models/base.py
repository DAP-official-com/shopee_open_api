import json


class ShopeeResponseBaseClass(json.JSONEncoder):
    """Shopee model base class for all shopee models"""

    def __init__(self, *initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
            for key, value in kwargs.items():
                setattr(self, key, value)

    def to_json(self):
        return json.loads(
            json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        )
