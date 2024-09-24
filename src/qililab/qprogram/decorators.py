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
            # Check if the parameter is not inside kwargs, for optional parameters
            if parameter not in kwargs and len(args) == 1:
                kwargs[parameter] = None
            # Get the argument by name
            param_value = kwargs.get(parameter) if parameter in kwargs else None

            if isinstance(param_value, Variable) and param_value.domain != domain:
                raise ValueError(f"Expected domain {domain} for {parameter}, but got {param_value.domain}")
            return func(*args, **kwargs)

        return wrapper

    return decorator_function
