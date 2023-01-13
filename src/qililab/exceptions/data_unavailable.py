"""DataUnavailable Exception class"""


class DataUnavailable(Exception):
    """Exception raised when a method is requesting data that is not available.

    Args:
        message (str): Optional message to be displayed
    """

    def __init__(self, message: str | None):
        super().__init__("Requesting data not available" if message is None else message)
