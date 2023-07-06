from typing import Any


class Variable:
    value: Any

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)

    def __add__(self, other):
        return self.value + other

    def __sub__(self, other):
        return self.value - other

    def __mul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other


class IntVariable(Variable, int):
    def __init__(self, value: int = 0):
        self.value: int = value
        super().__init__()


class FloatVariable(Variable, float):
    def __init__(self, value: float = 0):
        self.value: float = value
        super().__init__()
