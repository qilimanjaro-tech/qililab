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

import math

from qililab.core.variables import Variable
from qililab.qprogram.blocks.block import Block
from qililab.yaml import yaml


@yaml.register_class
class ForLoop(Block):
    def __init__(self, variable: Variable, start: int | float, stop: int | float, step: int | float) -> None:
        super().__init__()
        self.variable: Variable = variable
        self.start: int | float = start
        self.stop: int | float = stop
        self.step: int | float = step


def for_loop_iterations(start: int | float, stop: int | float, step: int | float) -> int:
    """Number of points a for_loop from ``start`` to ``stop`` by ``step`` sweeps.

    The count is rounded down whatever the sign of ``step``, so a loop never sweeps more points than its step allows
    and a descending loop sweeps as many points as its ascending mirror. A count within 1e-9 of an integer snaps to it,
    to absorb floating-point error (``0 -> 0.7`` by ``0.1`` is 8 points, not 7).

    A step pointing away from ``stop`` gives 0 points or fewer; callers decide how to handle it.

    Raises:
        ValueError: If ``step`` is zero.
    """
    if step == 0:
        raise ValueError("Step value cannot be zero")
    raw_iterations = (stop - start + step) / step
    if abs(raw_iterations - round(raw_iterations)) < 1e-9:
        return round(raw_iterations)
    return math.floor(raw_iterations)
