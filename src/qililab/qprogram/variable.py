from typing import Any


class Variable:
    value: Any

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.value


class IntVariable(Variable, int):
    def __init__(self, value: int = 0):
        self.value: int = value
        super().__init__()


class FloatVariable(Variable, float):
    def __init__(self, value: float = 0.0):
        self.value: float = value
        super().__init__()
