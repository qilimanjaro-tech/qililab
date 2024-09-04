import sys

# For Python 3.11+, we use ExceptionGroup; otherwise, we define a custom exception class
if sys.version_info >= (3, 11):
    # Available natively in Python 3.11+
    from exceptiongroup import ExceptionGroup  # pylint: disable=unused-import
else:
    # Define a custom exception class for earlier versions
    class ExceptionGroup(Exception):
        """Custom implementation of ExceptionGroup."""

        def __init__(self, message, exceptions):
            self.exceptions = exceptions
            super().__init__(f"{message}: {', '.join(str(e) for e in exceptions)}")
