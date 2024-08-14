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
from collections import deque

from qililab.qprogram.blocks import Block, ForLoop
from qililab.qprogram.variable import ValueSource, Variable
from qililab.yaml import yaml


@yaml.register_class
class Experiment:
    def __init__(self):
        self._body: Block = Block()
        self._variables: list[Variable] = []
        self._block_stack: deque[Block] = deque([self._body])

    def _append_to_block_stack(self, block: Block):
        self._block_stack.append(block)

    def _pop_from_block_stack(self):
        return self._block_stack.pop()

    @property
    def _active_block(self) -> Block:
        return self._block_stack[-1]

    def block(self):
        """Define a generic block for scoping operations.

        Blocks need to open a scope.

        Returns:
            Block: The block.

        Examples:

            >>> with qp.block() as block:
            >>>    # operations that shall be executed in the block
        """
        return Experiment._BlockContext(experiment=self)

    def for_loop(self, variable: Variable, start: int | float, stop: int | float, step: int | float = 1):
        """Define a for_loop block to iterate values over a variable.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            start (int | float): The start value.
            stop (int | float): The stop value.
            step (int | float, optional): The step value. Defaults to 1.

        Returns:
            Loop: The loop block.

        Examples:

            >>> variable = qp.variable(int)
            >>> with qp.for_loop(variable=variable, start=0, stop=100, step=5)):
            >>>    # operations that shall be executed in the for_loop block
        """

        return Experiment._ForLoopContext(experiment=self, variable=variable, start=start, stop=stop, step=step)

    class _BlockContext:
        def __init__(self, experiment: "Experiment"):
            self.experiment = experiment
            self.block: Block = Block()

        def __enter__(self):
            self.experiment._append_to_block_stack(block=self.block)
            return self.block

        def __exit__(self, exc_type, exc_value, exc_tb):
            block = self.experiment._pop_from_block_stack()
            self.experiment._active_block.append(block)

    class _ForLoopContext(_BlockContext):  # pylint: disable=too-few-public-methods
        def __init__(  # pylint: disable=super-init-not-called
            self, experiment: "Experiment", variable: Variable, start: int | float, stop: int | float, step: int | float
        ):
            self.experiment = experiment
            self.block: ForLoop = ForLoop(variable=variable, start=start, stop=stop, step=step)

        def __enter__(self) -> ForLoop:
            self.block.variable._source = ValueSource.Dependent
            self.block.variable._value = None
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.block.variable._source = ValueSource.Free
            super().__exit__(exc_type, exc_value, exc_tb)
