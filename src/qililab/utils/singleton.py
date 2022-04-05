from typing import Dict


class Singleton(type):
    """Singleton metaclass used to limit to 1 the number of instances of a subclass."""

    _instances: Dict = {}

    def __call__(cls, *args, **kwargs):
        """Create a new instance of cls if it doesn't already exist."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
