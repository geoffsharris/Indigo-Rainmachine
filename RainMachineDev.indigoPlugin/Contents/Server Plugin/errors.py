"""Define package errors."""


class RainMachineError(Exception):
    """Define a base error."""

    pass


class RequestError(RainMachineError):
    """Define an error related to invalid requests."""

    pass


class TokenExpiredError(RainMachineError):
    """Define an error for expired access tokens that can't be refreshed."""

    pass


ERROR_CODES = {1: "The email has not been validated",
               2: "no devices are connected to the cloud",
               3: "the password provided is wrong",
               4: "internal server error"}


def raise_remote_error(error_code):
    """Raise the appropriate error with a remote error code."""
    try:
        error = next((v for k, v in ERROR_CODES.items() if k == error_code))
        raise RequestError(error)
    except StopIteration:
        raise RequestError("Unknown remote error code returned: {}".format(error_code))
