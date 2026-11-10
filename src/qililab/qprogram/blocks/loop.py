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
"""The loop over explicit values ``qp.parallel`` takes."""

import numpy as np
from qprogram import Values, Variable


class Loop:
    """A loop over explicit ``values``, given to ``qp.parallel(loops=[...])``.

    Only an argument for the deprecated ``qp.parallel``: the program holds a qprogram ``Sweep`` over ``Values``, which
    qililab's capability profile does not support yet, so validation rejects it.

    Args:
        variable (Variable): The variable the loop sweeps.
        values (np.ndarray): The values to iterate over.
    """

    def __init__(self, variable: Variable, values: np.ndarray) -> None:
        self.variable: Variable = variable
        self.values: np.ndarray = values

    def to_values(self) -> Values:
        """Return the ``Values`` source that sweeps the loop's points.

        Returns:
            Values: The source holding ``values``.
        """
        return Values(self.values)
