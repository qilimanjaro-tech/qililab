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
"""VariableAllocated Exception class"""

from qprogram import Variable


class VariableAllocated(Exception):
    """Exception raised when a loop sweeps a variable an enclosing loop, or another loop of the same parallel block,
    already sweeps.

    Its name comes from the former variables, which loops marked as allocated while they swept them.

    Args:
        variable (Variable): The variable swept twice.
    """

    def __init__(self, variable: Variable) -> None:
        super().__init__(
            f"Variable {variable.id!r} is already swept by an enclosing loop or by another loop of the same parallel "
            "block: each loop needs its own variable."
        )
