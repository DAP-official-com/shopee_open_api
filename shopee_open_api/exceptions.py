from frappe.exceptions import ValidationError


class NotShopeeBranchError(Exception):
    pass


class BadRequestError(Exception):
    pass


class NotAuthorizedError(Exception):
    pass


class NoShopAuthorizedError(ValidationError):
    pass
