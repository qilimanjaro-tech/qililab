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

"""Loop class."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from qililab.constants import LOOP
from qililab.typings.enums import Parameter


@dataclass
class Loop:
    """Class used to loop a parameter over the given array values.

    Args:
        alias (str): Alias of the object holding the parameter to loop over.
        parameter (Parameter): Parameter to loop.
        values (ndarray): Array of values to loop over.
        loop (Loop | None): Inner loop. If not None, a nested loop is created. Defaults to None.

    **Examples**:
    Here is an example to create a loop over the frequency of the instrument 'AWG' with the given values:
    >>> loop = Loop(alias='AWG', parameter=Parameter.FREQUENCY, values=np.linspace(7e9, 8e9, num=10))

    Any array of values can be used. For example, one can use `np.logsapce` or `np.geomspace` to create a logarithmic
    loop:
    >>> loop = Loop(alias='AWG', parameter=Parameter.FREQUENCY, values=np.logspace(7e9, 8e9, num=10))

    The difference between `np.logspace` or `np.geomspace` is that geomspace specifies the exact start and stop
    points while logspace specifies the exponent of the start and stop given a base. See below:
    np.logspace(start=1, stop=5, num=5, base=2) -> [base**start .. base**stop] -> [2,4,8,16,32]
    np.geomspace(start=2, stop=32, num=5) -> [start .. stop] -> [2,4,8,16,32]

    One can also create nested loops:
    >>> inner_loop = Loop(alias='AWG', parameter=Parameter.FREQUENCY, values=np.arange(7e9, 8e9, step=10))
    >>> outer_loop = Loop(alias='AWG', parameter=Parameter.POWER, values=np.linspace(0, 10, num=10), loop=inner_loop)
    """

    alias: str
    parameter: Parameter
    values: np.ndarray
    loop: Loop | None = None
    previous: Loop | None = field(compare=False, default=None)
    channel_id: int | None = None

    def __post_init__(self):
        """Check that either step or num is used. Overwrite 'previous' attribute of next loop with self."""
        if self.loop is not None:
            if isinstance(self.loop, dict):
                self.loop = Loop(**self.loop)
            self.loop.previous = self
        if isinstance(self.parameter, str):
            self.parameter = Parameter(self.parameter)
        if isinstance(self.values, list):
            self.values = np.array(self.values, dtype=object)

    @property
    def all_values(self) -> np.ndarray:
        """Loop 'all_values' property.

        Returns:
            list: Values of all loops.
        """
        all_values = [loop.values for loop in self.loops]
        return np.array(all_values, dtype=object)

    @property
    def shape(self) -> list[int]:
        """Return number of points of all loops.

        Returns:
            list: List containing the number of points of all loops.
        """
        shape = []
        loop: Loop | None = self
        while loop is not None:
            shape.append(int(loop.num))
            loop = loop.loop
        return shape

    @property
    def num_loops(self) -> int:
        """Loop 'num_loops' property.

        Returns:
            int: Number of nested loops.
        """
        return len(self.loops)

    @property
    def loops(self) -> list[Loop]:
        """Loop 'loops' property.

        Returns:
            list[Loop]: List of loop objects.
        """
        loops = []
        loop: Loop | None = self
        while loop is not None:
            loops.append(loop)
            loop = loop.loop
        return loops

    def to_dict(self) -> dict:
        """Convert class to a dictionary.

        Returns:
            dict: Dictionary representation of the class.
        """
        return {
            LOOP.ALIAS: self.alias,
            LOOP.PARAMETER: self.parameter.value,
            LOOP.VALUES: self.values.tolist(),
            LOOP.LOOP: self.loop.to_dict() if self.loop is not None else None,
            LOOP.CHANNEL_ID: self.channel_id,
        }

    @property
    def start(self):
        """returns 'start' options property."""
        return self.values[0]

    @property
    def stop(self):
        """returns 'stop' options property."""
        return self.values[-1]

    @property
    def num(self):
        """returns 'num' options property."""
        return len(self.values)

    def __eq__(self, other: object) -> bool:
        """Equality operator"""
        if not isinstance(other, Loop):
            return False
        return (
            self.alias == other.alias
            and self.parameter == other.parameter
            and self.loop == other.loop
            and self.channel_id == other.channel_id
            and (self.values == other.values).all()
        )
