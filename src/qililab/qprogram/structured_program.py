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

import numpy as np

from qililab.core import Domain, FloatVariable, IntVariable, Variable
from qililab.exceptions import VariableAllocated
from qililab.qprogram.blocks import ForLoop, InfiniteLoop, Loop, Parallel
from qililab.yaml import yaml

from . import SdkStructuredProgram, VariableInfo


@yaml.register_class
class StructuredProgram(SdkStructuredProgram):
    """Represents a structured quantum program with various control flow blocks."""

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

    class _LoopContext(SdkStructuredProgram._BlockContext):
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

    class _InfiniteLoopContext(SdkStructuredProgram._BlockContext):
        def __init__(self, program: "StructuredProgram"):
            self.program = program
            self.block: InfiniteLoop = InfiniteLoop()

    class _ParallelContext(SdkStructuredProgram._BlockContext):
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
