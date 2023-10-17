import functools

from .variable import Domain, Variable


def requires_domain(parameter: str, domain: Domain):
    def get_nested_attr(obj, attrs):
        """Recursively get nested attributes."""
        if not attrs:
            return obj
        return get_nested_attr(getattr(obj, attrs[0]), attrs[1:])

    def decorator_function(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Split parameter and its attributes
            param_parts = parameter.split(".")
            param_name = param_parts[0]

            # Get the argument by name
            param_value = (
                kwargs.get(param_name) if param_name in kwargs else args[1]
            )  # assuming 1 is the default position

            # Fetch the (possibly nested) attribute value
            value_to_check = get_nested_attr(param_value, param_parts[1:])

            if isinstance(value_to_check, Variable) and value_to_check.domain != domain:
                raise ValueError(f"Expected domain {domain} for {parameter}, but got {value_to_check.domain}")
            return func(*args, **kwargs)

        return wrapper

    return decorator_function
