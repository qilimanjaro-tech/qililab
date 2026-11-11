# Copyright 2026 Qilimanjaro Quantum Tech
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
"""``+x`` is ``x``: the unary plus qililab's former variables ignored."""

from qprogram import BinaryOp, Expression, UnaryOp
from qprogram.operations import Operation


def without_unary_plus(expression: Expression) -> Expression:
    """Return ``expression`` without its unary ``+``, rebuilt only where one was removed.

    Args:
        expression (Expression): The expression.

    Returns:
        Expression: ``expression`` itself when it has no unary ``+``, else the same expression without them.
    """
    if isinstance(expression, UnaryOp):
        operand = without_unary_plus(expression.operand)
        if expression.op == "+":
            return operand
        return expression if operand is expression.operand else UnaryOp(expression.op, operand)
    if isinstance(expression, BinaryOp):
        left, right = without_unary_plus(expression.left), without_unary_plus(expression.right)
        if left is expression.left and right is expression.right:
            return expression
        return BinaryOp(expression.op, left, right)
    return expression


def drop_unary_plus(element: object) -> None:
    """Remove the unary ``+`` from the expressions an operation holds, in place: ``qp.set_gain(bus, +g)`` stores ``g``.

    qililab's former variables returned themselves for ``+x``. qprogram's keep it as an expression, which qililab's
    compilers don't take.

    Args:
        element (object): The operation or block being added to a program. Blocks are left as they are.
    """
    if not isinstance(element, Operation):
        return
    for name, value in list(vars(element).items()):
        if isinstance(value, Expression):
            setattr(element, name, without_unary_plus(value))
