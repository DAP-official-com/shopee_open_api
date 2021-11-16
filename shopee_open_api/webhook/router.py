from .exceptions import IncorrectWebhookCodeError
from .handlers import handle_order_status_update

router = {
    0: lambda _: True,
    1: lambda _: True,
    2: lambda _: True,
    3: handle_order_status_update,
    4: lambda _: True,
    5: lambda _: True,
    6: lambda _: True,
    7: lambda _: True,
    8: lambda _: True,
    9: lambda _: True,
    10: lambda _: True,
    11: lambda _: True,
    12: lambda _: True,
    13: lambda _: True,
}


def get_webhook_handler(code: int):

    if code not in range(0, 14):
        raise IncorrectWebhookCodeError(f"The code {code} was incorrect")

    if router.get(code, False) == False:
        raise NotImplementedError(f"There is no implementation for code {code}")

    return router.get(code)
