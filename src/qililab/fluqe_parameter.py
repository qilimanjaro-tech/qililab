""" Basic implementation of a qcodes like parameter class, but much simpler.
Working, but still work in progress
"""

from typing import Any, Callable


class Parameter:
    def __init__(self, name, value=None, set_method: Callable | None = None):
        # TODO: add units and other useful info
        self.name = name
        self._value = value
        self.set = set_method

    def __call__(self, *args, **kwargs: Any) -> None:
        # TODO: implement get_raw like in qcodes
        if args or kwargs:
            self._value = self.set(*args, **kwargs) if self.set is not None else self.set_raw(args[0])

        else:
            return self.get(*args, **kwargs)

    def get(self):
        return self._value

    def set_raw(self, value):
        self._value = value
        return value
