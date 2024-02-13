import functools

from .variable import Domain, Variable


def requires_domain(parameter: str, domain: Domain):
    """Decorator to denote that a parameter requires a variable of a specific domain.

    Args:
        parameter (str): The parameter name.
        domain (Domain): The variable's domain.
    """

    def decorator_function(func):
        # Check if the original function is a classmethod
        if isinstance(func, classmethod):
            original_func = func.__func__
        else:
            original_func = func

        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            # Determine if we're working with a class or instance method
            cls_or_self = args[0]

            # Get the argument by name
            param_value = kwargs.get(parameter)

            if param_value is not None and isinstance(param_value, Variable) and param_value.domain != domain:
                raise ValueError(f"Expected domain {domain} for {parameter}, but got {param_value.domain}")

            # If it's a classmethod, call it as such
            if isinstance(func, classmethod):
                return original_func(cls_or_self, *args[1:], **kwargs)
            else:
                return original_func(*args, **kwargs)

        # If the original function was a classmethod, return it as a classmethod
        if isinstance(func, classmethod):
            return classmethod(wrapper)
        else:
            return wrapper

    return decorator_function
