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
"""The points of the deprecated ``for_loop``."""

import math
import numbers
from typing import cast

from qprogram import Linspace


def to_scalar(value: object) -> object:
    """Convert a number, numpy ones included, to a Python ``int`` or ``float``; return anything else unchanged.

    Values often come from numpy, and qprogram refuses a numpy integer as a number of shots and stores other numpy
    numbers as they are (QHC-1873).

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


def for_loop_linspace(start: int | float, stop: int | float, step: int | float) -> Linspace:
    """Return the ``Linspace`` a for_loop from ``start`` to ``stop`` by ``step`` sweeps.

    A for_loop sweeps ``for_loop_iterations`` points, rounded down, spread evenly from ``start`` to ``stop``: the step
    the user wrote when it divides ``stop - start``.

    Args:
        start (int | float): First value of the loop.
        stop (int | float): Last value of the loop.
        step (int | float): Increment between consecutive values.

    Returns:
        Linspace: The loop's points.

    Raises:
        ValueError: If ``step`` is zero.
        ValidationError: If ``step`` points away from ``stop``, which leaves no point to sweep.
    """
    start, stop, step = (cast("int | float", to_scalar(value)) for value in (start, stop, step))
    return Linspace(start, stop, for_loop_iterations(start, stop, step))


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
