from frappe.exceptions import ValidationError


class NotShopeeBranchError(Exception):
    pass


class BadRequestError(Exception):
    pass


class NotAuthorizedError(Exception):
    pass


class NoShopAuthorizedError(ValidationError):
    pass


class OrderAutomationProcessingError(ValidationError):
    pass


class AlreadyHasSalesOrderError(OrderAutomationProcessingError):
    pass


class ProductHasNoItemError(OrderAutomationProcessingError):
    pass


class ItemHasNoPriceError(OrderAutomationProcessingError):
    pass
