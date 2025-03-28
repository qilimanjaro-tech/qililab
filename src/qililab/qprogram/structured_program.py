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

import numpy as np

from qililab.exceptions.variable_allocated import VariableAllocated
from qililab.qprogram.blocks import Average, Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.variable import Domain, FloatVariable, IntVariable, Variable
from qililab.yaml import yaml


@yaml.register_class
class VariableInfo:
    def __init__(self) -> None:
        self.is_allocated: bool = False
        self.allocated_by: Block | None = None

    def allocate(self, block: Block):
        self.is_allocated = True
        self.allocated_by = block

    def free(self):
        self.is_allocated = False
        self.allocated_by = None


@yaml.register_class
class StructuredProgram:
    """Represents a structured quantum program with various control flow blocks."""

    def __init__(self) -> None:
        """Initializes a StructuredProgram instance, setting up the body, block stack, variables, and buses."""
        self._body: Block = Block()
        self._block_stack: deque[Block] = deque([self._body])
        self._variables: dict[Variable, VariableInfo] = {}
        self._buses: set[str] = set()

    def _append_to_block_stack(self, block: Block):
        """Appends a block to the internal block stack.

        Args:
            block (Block): The block to append.
        """
        self._block_stack.append(block)

    def _pop_from_block_stack(self):
        """Removes and returns the last block from the block stack.

        Returns:
            Block: The popped block.
        """
        return self._block_stack.pop()

    @property
    def _active_block(self) -> Block:
        """Returns the currently active block on top of the block stack.

        Returns:
            Block: The active block.
        """
        return self._block_stack[-1]

    @property
    def body(self) -> Block:
        """Get the body of the QProgram

        Returns:
            Block: The block of the body
        """
        return self._body

    @property
    def buses(self) -> set[str]:
        """Get the buses.

        Returns:
            set[str]: A set of the names of the buses
        """
        return self._buses

    @property
    def variables(self) -> list[Variable]:
        """Get the variables.

        Returns:
            list[Variable]: A list of variables
        """
        return list(self._variables)

    def insert_block(self, block: Block):
        self._active_block.append(block)

    def block(self):
        """Define a generic block for scoping operations.

        Blocks need to open a scope.

        Returns:
            Block: The block.

        Examples:

            >>> with qp.block() as block:
            >>> # operations that shall be executed in the block
        """
        return StructuredProgram._BlockContext(program=self)

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
            >>> # operations that shall be executed in the for_loop block
        """

        return StructuredProgram._ForLoopContext(program=self, variable=variable, start=start, stop=stop, step=step)

    def loop(self, variable: Variable, values: np.ndarray):
        """Define a loop block to iterate values over a variable.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            values (np.ndarray): The values to iterate over.

        Returns:
            Loop: The loop block.

        Examples:

            >>> variable = qp.variable(int)
            >>> with qp.loop(variable=variable, values=np.array(range(100))):
            >>> # operations that shall be executed in the loop block
        """

        return StructuredProgram._LoopContext(program=self, variable=variable, values=values)

    def infinite_loop(self):
        """Define an infinite loop.

        Blocks need to open a scope.

        Examples:

            >>> with qp.infinite_loop():
            >>> # operations that shall be executed in the infinite loop block

        Returns:
            InfiniteLoop: The infinite loop block.
        """
        return StructuredProgram._InfiniteLoopContext(program=self)

    def parallel(self, loops: list[Loop | ForLoop]):
        """Define a block for running multiple loops in parallel.

        Blocks need to open a scope.

        Examples:
            >>> gain = qp.variable(float)
            >>> frequency = qp.variable(float)
            >>> with qp.parallel(loops=[ForLoop(variable=frequency, start=0, stop=100, step=10),
                                        ForLoop(variable=gain, start=0.0, stop=1.0, step=0.1)]):
            >>> # operations that shall be executed in the block

        Args:
            loops (list[Loop  |  ForLoop]): The loops to run in parallel

        Returns:
            Parallel: The parallel block.
        """
        return StructuredProgram._ParallelContext(program=self, loops=loops)

    def average(self, shots: int):
        """Define an acquire loop block with averaging in real time.

        Blocks need to open a scope.

        Args:
            iterations (int): The number of acquire iterations.

        Returns:
            Average: The average block.

        Examples:

            >>> with qp.average(shots=1000):
            >>> # operations that shall be executed in the average block
        """
        return StructuredProgram._AverageContext(program=self, shots=shots)

    def variable(self, label: str, domain: Domain, type: type[int | float] | None = None):
        """Declare a variable.

        Args:
            type (int | float): The type of the variable.

        Raises:
            NotImplementedError: If an unsupported type is provided.

        Returns:
            IntVariable | FloatVariable: The variable.
        """

        def _int_variable(label: str, domain: Domain = Domain.Scalar) -> IntVariable:
            variable = IntVariable(label, domain)
            self._variables[variable] = VariableInfo()
            return variable

        def _float_variable(label: str, domain: Domain = Domain.Scalar) -> FloatVariable:
            variable = FloatVariable(label, domain)
            self._variables[variable] = VariableInfo()
            return variable

        if domain is Domain.Scalar and type is None:
            raise ValueError("You must specify a type in a scalar variable.")
        if domain is not Domain.Scalar and type is not None:
            raise ValueError("When declaring a variable of a specific domain, its type is inferred by its domain.")

        if domain is Domain.Scalar:
            if type is int:
                return _int_variable(label, domain)
            if type is float:
                return _float_variable(label, domain)

        if domain == Domain.Time:
            return _int_variable(label, domain)
        if domain in [Domain.Frequency, Domain.Phase, Domain.Voltage, Domain.Flux]:
            return _float_variable(label, domain)
        raise NotImplementedError

    class _BlockContext:
        def __init__(self, program: "StructuredProgram"):
            self.program = program
            self.block: Block = Block()

        def __enter__(self):
            self.program._append_to_block_stack(block=self.block)
            return self.block

        def __exit__(self, exc_type, exc_value, exc_tb):
            block = self.program._pop_from_block_stack()
            self.program._active_block.append(block)

    class _ForLoopContext(_BlockContext):
        def __init__(
            self,
            program: "StructuredProgram",
            variable: Variable,
            start: int | float,
            stop: int | float,
            step: int | float,
        ):
            self.program = program
            self.block: ForLoop = ForLoop(variable=variable, start=start, stop=stop, step=step)

        def __enter__(self) -> ForLoop:
            if self.program._variables[self.block.variable].is_allocated:
                raise VariableAllocated(self.block.variable)
            self.program._variables[self.block.variable].allocate(self.block)
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.program._variables[self.block.variable].free()
            super().__exit__(exc_type, exc_value, exc_tb)

    class _LoopContext(_BlockContext):
        def __init__(self, program: "StructuredProgram", variable: Variable, values: np.ndarray):
            self.program = program
            self.block: Loop = Loop(variable=variable, values=values)

        def __enter__(self) -> Loop:
            if self.program._variables[self.block.variable].is_allocated:
                raise VariableAllocated(self.block.variable)
            self.program._variables[self.block.variable].allocate(self.block)
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.program._variables[self.block.variable].free()
            super().__exit__(exc_type, exc_value, exc_tb)

    class _InfiniteLoopContext(_BlockContext):
        def __init__(self, program: "StructuredProgram"):
            self.program = program
            self.block: InfiniteLoop = InfiniteLoop()

    class _ParallelContext(_BlockContext):
        def __init__(self, program: "StructuredProgram", loops: list[Loop | ForLoop]):
            self.program = program
            self.block: Parallel = Parallel(loops=loops)

        def __enter__(self) -> Parallel:
            for loop in self.block.loops:
                if self.program._variables[loop.variable].is_allocated:
                    raise VariableAllocated(loop.variable)
                self.program._variables[loop.variable].allocate(loop)
            return super().__enter__()

        def __exit__(self, exc_type, exc_value, exc_tb):
            for loop in self.block.loops:
                self.program._variables[loop.variable].free()
            super().__exit__(exc_type, exc_value, exc_tb)

    class _AverageContext(_BlockContext):
        def __init__(self, program: "StructuredProgram", shots: int):
            self.program = program
            self.block: Average = Average(shots=shots)
