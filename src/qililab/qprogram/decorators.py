import functools

from .variable import Domain, Variable


def requires_domain(parameter: str, domain: Domain):
    """Decorator to denote that a parameter requires a variable of a specific domain.

    Args:
        parameter (str): The parameter name.
        domain (Domain): The variable's domain.
    """

    def decorator_function(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the argument by name
            param_value = (
                kwargs.get(parameter) if parameter in kwargs else args[1]
            )  # assuming 1 is the default position

            if isinstance(param_value, Variable) and param_value.domain != domain:
                raise ValueError(f"Expected domain {domain} for {parameter}, but got {param_value.domain}")
            return func(*args, **kwargs)

        return wrapper

    return decorator_function
