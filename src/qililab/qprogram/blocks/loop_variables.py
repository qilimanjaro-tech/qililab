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
"""The variables a loop sweeps, and the check that nested loops sweep different ones."""

from collections.abc import Iterable

from qprogram import Variable
from qprogram.blocks import Block, Parallel, Sweep

from qililab.exceptions.variable_allocated import VariableAllocated


def swept_variables(block: Block) -> list[Variable]:
    """Return the variables ``block`` sweeps: a sweep's one, each of a parallel's loops, none for another block.

    Args:
        block (Block): The block.

    Returns:
        list[Variable]: The variables it sweeps.
    """
    if isinstance(block, Parallel):
        return [loop.variable for loop in block.loops]
    if isinstance(block, Sweep):
        return [block.variable]
    return []


def reject_variables_swept_by_enclosing_loops(element: object, enclosing: Iterable[Block]) -> None:
    """Raise if ``element`` is a loop over a variable one of the ``enclosing`` blocks, or the loop itself, already sweeps.

    Args:
        element (object): The element being added.
        enclosing (Iterable[Block]): The blocks it is added in.

    Raises:
        VariableAllocated: If the loop sweeps a variable an enclosing loop already sweeps.
    """
    if not isinstance(element, Block):
        return
    swept = {variable.id for block in enclosing for variable in swept_variables(block)}
    for variable in swept_variables(element):
        if variable.id in swept:
            raise VariableAllocated(variable)
        # a parallel cannot sweep one variable twice either
        swept.add(variable.id)
