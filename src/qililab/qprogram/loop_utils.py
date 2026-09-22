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
"""Shared helpers to enumerate ``ForLoop`` sweeps consistently across the codebase.

Every place that needs to know how many points a ``ForLoop`` runs (compilers,
crosstalk compensation, experiment executor) must agree, otherwise result arrays
sized in one place fail to match data produced in another. These helpers are the
single source of truth for that count and for the swept values.
"""

import math

import numpy as np


def calculate_iterations(start: int | float, stop: int | float, step: int | float) -> int:
    """Number of points a ``ForLoop(start, stop, step)`` runs, ``stop`` inclusive.

    Args:
        start (int | float): First value of the sweep.
        stop (int | float): Last value of the sweep (inclusive).
        step (int | float): Increment between consecutive values.

    Returns:
        int: The number of iterations.
    """
    if step == 0:
        raise ValueError("Step value cannot be zero")

    # Raw count; rounded to the nearest integer when floating-point error keeps it close to one.
    raw_iterations = (stop - start + step) / step
    if abs(raw_iterations - round(raw_iterations)) < 1e-9:
        return round(raw_iterations)

    # Otherwise incrementing sweeps take the floor and decrementing sweeps the ceiling.
    return math.floor(raw_iterations) if step > 0 else math.ceil(raw_iterations)


def loop_range(start: int | float, stop: int | float, step: int | float) -> np.ndarray:
    """Values a ``ForLoop(start, stop, step)`` runs, ``stop`` inclusive.

    Uses ``np.linspace`` over :func:`calculate_iterations` points instead of a half-open
    ``np.arange`` so the last value lands exactly on ``stop`` and the length always matches
    the number of iterations the compilers execute.

    Args:
        start (int | float): First value of the sweep.
        stop (int | float): Last value of the sweep (inclusive).
        step (int | float): Increment between consecutive values.

    Returns:
        np.ndarray: The swept values. Empty when the parameters describe no iterations
            (e.g. a step pointing away from ``stop``).
    """
    return np.linspace(start, stop, max(calculate_iterations(start, stop, step), 0))
