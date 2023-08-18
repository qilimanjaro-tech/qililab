"""Nested dataclass decorator."""
from dataclasses import dataclass, is_dataclass
from typing import get_type_hints


def nested_dataclass(*args, **kwargs):
    """Class decorator used to cast any dict/str attributes into its corresponding dataclass/enum classes."""

    def wrapper(cls):
        """Class wrapper."""
        cls = dataclass(cls, **kwargs)
        original_init = cls.__init__

        def __init__(self, *args, **kwargs):
            for name, value in kwargs.items():
                field_type = get_type_hints(cls).get(name, None)
                if is_dataclass(field_type):
                    new_obj = field_type(**value)
                    kwargs[name] = new_obj
            original_init(self, *args, **kwargs)

        cls.__init__ = __init__
        return cls

    return wrapper(args[0]) if args else wrapper
