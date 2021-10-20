from .exceptions import IncorrectWebhookCodeError
from .handlers import handle_order_status_update

router = {
    0: lambda _: True,
    3: handle_order_status_update,
}


def get_webhook_handler(code: int):

    if code not in range(0, 14):
        raise IncorrectWebhookCodeError(f"The code {code} was incorrect")

    if router.get(code, False) == False:
        raise NotImplementedError(f"There is no implementation for code {code}")

    return router.get(code)
