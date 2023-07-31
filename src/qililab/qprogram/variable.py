"""This file contains all the variables used inside a QProgram."""
from typing import Any


class Variable:
    """Variable class used to define variables inside a QProgram."""

    value: Any

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)


class IntVariable(Variable, int):
    """Integer variable. This class is used to define a variable of type int, such that Python recognizes this class
    as an integer."""

    def __init__(self, value: int = 0):
        self.value: int = value
        super().__init__()


class FloatVariable(Variable, float):
    """Float variable. This class is used to define a variable of type float, such that Python recognizes this class
    as a float."""

    def __init__(self, value: float = 0.0):
        self.value: float = value
        super().__init__()
