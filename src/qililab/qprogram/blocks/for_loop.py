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
"""The ``for_loop`` point count, and the loop description ``qp.parallel`` takes."""

import math
import numbers

from qprogram import Range, Variable


def to_scalar(value: object) -> object:
    """Convert a number, numpy ones included, to a Python ``int`` or ``float``; return anything else unchanged.

    qprogram refuses numpy integers where it takes a number, and loop bounds often come from numpy.

    Args:
        value (object): The value to convert.

    Returns:
        object: ``int(value)`` for an integral number, ``float(value)`` for a real one, else ``value``.
    """
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        return value
    if isinstance(value, numbers.Integral):
        return int(value)
    return float(value)


class ForLoop:
    """A loop from ``start`` to ``stop`` by ``step``, given to ``qp.parallel(loops=[...])``.

    Only an argument for the deprecated ``qp.parallel``: the program holds a qprogram ``Sweep`` over a ``Range``.

    Args:
        variable (Variable): The variable the loop sweeps.
        start (int | float): First value of the loop.
        stop (int | float): Last value of the loop.
        step (int | float): Increment between consecutive values.
    """

    def __init__(self, variable: Variable, start: int | float, stop: int | float, step: int | float) -> None:
        self.variable: Variable = variable
        self.start: int | float = to_scalar(start)  # type: ignore[assignment]
        self.stop: int | float = to_scalar(stop)  # type: ignore[assignment]
        self.step: int | float = to_scalar(step)  # type: ignore[assignment]

    def to_range(self) -> Range:
        """Return the ``Range`` that sweeps the same points as the loop.

        The range is first checked with the values the user wrote, so a step pointing away from ``stop`` raises
        ``ValidationError`` naming that step. A for_loop sweeps ``for_loop_iterations`` points (rounded down, where
        ``Range`` rounds to the nearest) spread evenly from ``start`` to ``stop``, so the step is then adjusted to
        ``(stop - start) / (points - 1)``: the step the user wrote when it divides ``stop - start``.

        Returns:
            Range: The range with the loop's start, stop and point count.

        Raises:
            ValidationError: If ``step`` is zero or points away from ``stop``.
        """
        Range(self.start, self.stop, self.step)
        points = for_loop_iterations(self.start, self.stop, self.step)
        if points == 1:
            return Range(self.start, self.start, self.step)
        return Range(self.start, self.stop, (self.stop - self.start) / (points - 1))


def for_loop_iterations(start: int | float, stop: int | float, step: int | float) -> int:
    """Number of points a for_loop from ``start`` to ``stop`` by ``step`` sweeps.

    The count is rounded down whatever the sign of ``step``, so a loop never sweeps more points than its step allows
    and a descending loop sweeps as many points as its ascending mirror. A count within 1e-9 of an integer snaps to it,
    to absorb floating-point error (``0 -> 0.7`` by ``0.1`` is 8 points, not 7).

    Args:
        start (int | float): First value of the loop.
        stop (int | float): Last value of the loop.
        step (int | float): Increment between consecutive values, negative for a descending loop.

    Returns:
        int: The number of points, 0 or fewer when ``step`` points away from ``stop``; callers decide how to handle
            that.

    Raises:
        ValueError: If ``step`` is zero.
    """
    if step == 0:
        raise ValueError("Step value cannot be zero")
    raw_iterations = (stop - start + step) / step
    if abs(raw_iterations - round(raw_iterations)) < 1e-9:
        return round(raw_iterations)
    return math.floor(raw_iterations)
