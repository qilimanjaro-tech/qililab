from functools import wraps


def check_device_initialized(method):
    """
    Function decorator to check if the device has been initialized.

    Args:
        method (Callable): The method to be decorated.

    Raises:
        AttributeError: If the device has not been initialized.
    """

    @wraps(method)
    def wrapped_function(ref, *args, **kwargs):
        # Check if the device has been initialized, similar to the class-based implementation.
        # The check is adjusted to directly use 'ref' and 'args' as applicable.
        if not hasattr(ref, "device") and (not args or not hasattr(args[0], "device")):
            raise AttributeError("Instrument Device has not been initialized")
        # Call the original method if the device is initialized.
        return method(ref, *args, **kwargs) if hasattr(ref, "device") else method(*args, **kwargs)

    return wrapped_function
