# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This file contains all the variables used inside a QProgram."""
from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4

from qililab.yaml import yaml


@yaml.register_class
class Domain(Enum):
    """Domain class."""

    Scalar = 0
    Time = 1
    Frequency = 2
    Phase = 3
    Voltage = 4
    Flux = 5

    @classmethod
    def to_yaml(cls, representer, node):
        """Method to be called automatically during YAML serialization."""
        return representer.represent_scalar("!Domain", f"{node.name}-{node.value}")

    @classmethod
    def from_yaml(cls, _, node):
        """Method to be called automatically during YAML deserialization."""
        _, value = node.value.split("-")
        value = int(value)
        return cls(value)


def _validate_elements(elements: list[Variable | int]) -> None:
    for element in elements:
        if isinstance(element, VariableExpression):
            raise NotImplementedError(
                "Chaining Variable expressions is not supported; use at most one binary operation."
            )
        if isinstance(element, bool) or not isinstance(element, (Variable, int)):
            raise ValueError("Constants must be integers.")


def _unsupported_operation(operation_name: str):
    def method(self, *args, **kwargs):
        raise NotImplementedError(
            f"Operation '{operation_name}' is not implemented for QProgram."
        )
    return method


@yaml.register_class
class Variable:
    """Variable class used to define variables inside a QProgram."""
    def __init__(self, label: str, domain: Domain = Domain.Scalar) -> None:
        self._uuid: UUID = uuid4()
        self._label: str = label
        self._domain: Domain = domain

    def __repr__(self):
        return f"Variable(uuid={self.uuid!r}, label={self.label}, domain={self.domain})"

    def __hash__(self):
        return hash(self._uuid)

    def __eq__(self, other):
        return other is not None and isinstance(other, Variable) and self._uuid == other._uuid

    def __add__(self, other):
        _validate_elements([self, other])
        if isinstance(other, int) and other < 0:  # in the case where we have variable + (-cst)
            return VariableExpression(self, "-", abs(other))
        return VariableExpression(self, "+", other)

    def __radd__(self, other):
        # order change because Q1ASM can only have a register as first argument, changing it here avoids additional code in the qblox compiler
        _validate_elements([self, other])
        if isinstance(other, int) and other < 0:
            # deals with the case -cst +gain to reorganise it as gain - cst to simplify the assembly
            return VariableExpression(self, "-", abs(other))
        return VariableExpression(self, "+", other)

    def __sub__(self, other):
        _validate_elements([self, other])
        if isinstance(other, int) and other < 0:
            return VariableExpression(self, "+", abs(other))
        return VariableExpression(self, "-", other)

    def __rsub__(self, other):
        _validate_elements([self, other])
        return VariableExpression(other, "-", self)

    # Unsupported operations
    __mul__ = _unsupported_operation("multiplication (*)")
    __matmul__ = _unsupported_operation("matrix multiplication (@)")
    __truediv__ = _unsupported_operation("division (/)")
    __floordiv__ = _unsupported_operation("floor division (//)")
    __mod__ = _unsupported_operation("modulo (%)")
    __pow__ = _unsupported_operation("power (**)")
    __and__ = _unsupported_operation("bitwise and (&)")
    __or__ = _unsupported_operation("bitwise or (|)")
    __xor__ = _unsupported_operation("bitwise xor (^)")
    __lshift__ = _unsupported_operation("left shift (<<)")
    __rshift__ = _unsupported_operation("right shift (>>)")
    __gt__ = _unsupported_operation("greater-than (>)")
    __ge__ = _unsupported_operation("greater-or-equal (>=)")
    __rmul__ = _unsupported_operation("reflected multiplication (*)")
    __rtruediv__ = _unsupported_operation("reflected division (/)")
    __iadd__ = _unsupported_operation("in-place addition (+=)")
    __isub__ = _unsupported_operation("in-place subtraction (-=)")
    __imul__ = _unsupported_operation("in-place multiplication (*=)")
    __itruediv__ = _unsupported_operation("in-place division (/=)")

    @property
    def uuid(self):
        """Get the uuid of the variable

        Returns:
            UUID: The uuid of the variable
        """
        return self._uuid

    @property
    def label(self):
        """Get the label of the variable

        Returns:
            str: The label of the variable
        """
        return self._label

    @property
    def domain(self):
        """Get the domain of the variable

        Returns:
            Domain: The domain of the variable
        """
        return self._domain


@yaml.register_class
class IntVariable(Variable, int):  # type: ignore
    """Integer variable. This class is used to define a variable of type int, such that Python recognizes this class
    as an integer."""

    def __new__(cls, _: str = "", __: Domain = Domain.Scalar):
        # Create a new float instance
        instance = int.__new__(cls, 0)
        return instance

    def __init__(self, label: str = "", domain: Domain = Domain.Scalar):
        Variable.__init__(self, label, domain)

    # Unary operators must be defined on IntVariable itself. FloatVariable inherits from float, CPython uses the float numeric slots for unary slots.
    def __neg__(self):
        return VariableExpression(0, "-", self)

    def __pos__(self):
        return self

    def __abs__(self):
        raise NotImplementedError(
            "Taking the absolute of a variable is not implemented in QProgram."
        )


@yaml.register_class
class FloatVariable(Variable, float):  # type: ignore
    """Float variable. This class is used to define a variable of type float, such that Python recognizes this class
    as a float."""

    def __new__(cls, _: str = "", __: Domain = Domain.Scalar):
        # Create a new int instance
        instance = float.__new__(cls, 0.0)
        return instance

    def __init__(self, label: str = "", domain: Domain = Domain.Scalar):
        Variable.__init__(self, label, domain)

    # Unary operators must be defined on FloatVariable itself. FloatVariable inherits from float, CPython uses the float numeric slots for unary slots.
    def __neg__(self):
        return VariableExpression(0, "-", self)

    def __pos__(self):
        return self

    def __abs__(self):
        raise NotImplementedError(
            "Taking the absolute of a variable is not implemented in QProgram."
        )


@yaml.register_class
class VariableExpression(Variable):
    """An expression combining Variables and/or constants."""

    # TODO: The possible operations are very limited, they could be expanded with * or / if needed; and it could allow for parenthesis in the expression
    def __init__(self, left: Variable | int, operator: str, right: Variable | int):
        if isinstance(left, VariableExpression) or isinstance(right, VariableExpression):
            raise NotImplementedError(
                "Chaining Variable expressions is not supported; use at most one binary operation."
            )
        self.left = left
        self.operator = operator
        self.right = right
        domain = self._infer_domain()
        self._domain = domain
        if domain not in {Domain.Time, Domain.Voltage}:
            raise NotImplementedError(f"For the {domain.name} domain, VariableExpression is not supported yet.")
        super().__init__(label="", domain=self._domain)
        self.variables = self._extract_variables()
        self.components = self._extract_components()
        self.constant = self._extract_constant()

    def __repr__(self):
        return f"({self.left} {self.operator} {self.right})"

    def _infer_domain(self) -> Domain:
        domain_list = []

        def _collect_domain(expr):
            if isinstance(expr, VariableExpression):
                _collect_domain(expr.left)
                _collect_domain(expr.right)
            elif isinstance(expr, Variable):
                domain_list.append(expr.domain)

        _collect_domain(self)
        if not domain_list:
            raise ValueError("Cannot infer domain from constants.")

        domain = domain_list[0]
        if domain_list and not all(dom == domain_list[0] for dom in domain_list):
            raise ValueError("All variables should have the same domain.")
        if domain == Domain.Time and len(domain_list) > 1:
            raise NotImplementedError(f"For the {domain.name} domain, combining several variables in one expression is not implemented.")
        if len(domain_list) > 2:
            raise NotImplementedError(f"For the {domain.name} domain, Variable Expression currently supports up to two variables only.")
        return domain

    def _extract_variables(self) -> list[Variable]:
        """Recursively extract all Variable instances used in this expression."""
        variables = []

        def _collect(expr):
            if isinstance(expr, VariableExpression):
                _collect(expr.left)
                _collect(expr.right)
            elif isinstance(expr, Variable):
                variables.append(expr)

        _collect(self)
        if not variables:
            raise ValueError(f"No Variable instance found in expression: {self}")
        return variables

    def _extract_constant(self) -> int | None:
        """Recursively extract the constant used in this expression."""
        # If qprogram allows nested/chained operations, and hence having more than one constant, this function should be modified to return a list.
        def _collect(expr):
            if isinstance(expr, VariableExpression):
                result = _collect(expr.left)
                if result is not None:
                    return result
                return _collect(expr.right)
            if isinstance(expr, int) and not isinstance(expr, IntVariable):
                return expr
            return None

        result = _collect(self)
        return result

    def _extract_components(self) -> list[Variable | int]:
        """Recursively extract all components (variables and constants) used in this expression."""

        component = []

        def _collect(expr):
            if isinstance(expr, VariableExpression):
                _collect(expr.left)
                _collect(expr.right)
            else:
                component.append(expr)

        _collect(self)
        return component
