import math
from typing import Any


class Variable:
    value: int | float

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    def __format__(self, formatstr):
        return self.value.__format__(formatstr)

    def __pos__(self):
        return +self.value

    def __neg__(self):
        return -self.value

    def __abs__(self):
        return abs(self.value)

    def __round__(self, ndigits=None):
        return round(self.value, ndigits)

    def __floor__(self):
        return math.floor(self.value)

    def __ceil__(self):
        return math.ceil(self.value)

    def __trunc__(self):
        return math.trunc(self.value)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __complex__(self):
        return complex(self.value)

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __floordiv__(self, other):
        return self.value // other

    def __mod__(self, other):
        return self.value % other

    def __pow__(self, other):
        return self.value**other

    def __radd__(self, other):
        return other + self.value

    def __rsub__(self, other):
        return other - self.value

    def __rmul__(self, other):
        return other * self.value

    def __rtruediv__(self, other):
        return other / self.value

    def __rfloordiv__(self, other):
        return other // self.value

    def __rmod__(self, other):
        return other % self.value

    def __rpow__(self, other):
        return other**self.value

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __lt__(self, other):
        return self.value < other

    def __gt__(self, other):
        return self.value > other

    def __le__(self, other):
        return self.value <= other

    def __ge__(self, other):
        return self.value >= other


class IntVariable(Variable, int):  # type: ignore
    def __init__(self, value: int = 0):
        self.value: int = value
        super().__init__()


class FloatVariable(Variable, float):  # type: ignore
    def __init__(self, value: float = 0.0):
        self.value: float = value
        super().__init__()
