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
"""Experiment: platform parameter changes and QProgram executions, looped over on the PC."""

import functools
import operator
import re
from collections.abc import Sequence
from typing import Any, Callable

import numpy as np
import qprogram as qp
from qprogram import Values, Variable

from qililab.qprogram.blocks import ForLoop, Loop, reject_variables_swept_by_enclosing_loops
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.operations import ExecuteQProgram, GetParameter, SetParameter
from qililab.qprogram.operations.set_crosstalk import SetCrosstalk
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.unary_plus import drop_unary_plus
from qililab.typings.enums import Parameter
from qililab.yaml import yaml


@yaml.register_class
class Experiment(qp.QProgram):
    """Represents an experiment.

    This class allows setting platform parameters and executing quantum programs, in loops run on the PC by the
    ``ExperimentExecutor``.

    Args:
        label (str): The label of the experiment.
        description (str | None, optional): A description of the experiment. Defaults to None.
    """

    def __init__(self, label: str, description: str | None = None) -> None:
        super().__init__(label=label, description=description)

    def _append_to_active(self, element: Any) -> None:
        """Append ``element`` to the active block, refusing a loop over a variable an enclosing loop already sweeps.

        A unary ``+`` in the expressions of an operation is dropped, as qililab's former variables did: ``+x`` is ``x``.

        Args:
            element (Any): The operation or block to append.

        Raises:
            VariableAllocated: If ``element`` is a loop over a variable an enclosing loop already sweeps.
        """
        reject_variables_swept_by_enclosing_loops(element, self._block_stack)
        drop_unary_plus(element)
        super()._append_to_active(element)

    def for_loop(self, variable: Variable, start: int | float, stop: int | float, step: int | float = 1) -> Any:
        """Loop ``variable`` from ``start`` to ``stop`` by ``step``.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            start (int | float): The start value.
            stop (int | float): The stop value.
            step (int | float, optional): The step value. Defaults to 1.

        Returns:
            The context manager opening the ``Sweep`` block.
        """
        return self.sweep(variable, ForLoop(variable, start, stop, step).to_range())

    def loop(self, variable: Variable, values: np.ndarray) -> Any:
        """Loop ``variable`` over ``values``.

        Blocks need to open a scope.

        Args:
            variable (Variable): The variable to be affected from the loop.
            values (np.ndarray): The values to iterate over.

        Returns:
            The context manager opening the ``Sweep`` block.
        """
        return self.sweep(variable, Values(values))

    def parallel(self, loops: Sequence[ForLoop | Loop]) -> Any:
        """Run several loops in lockstep.

        Blocks need to open a scope.

        Args:
            loops (Sequence[ForLoop | Loop]): The loops to run in parallel.

        Returns:
            The context manager opening the ``Parallel`` block, or the ``Sweep`` block for a single loop.
        """
        contexts = [
            self.sweep(loop.variable, loop.to_range() if isinstance(loop, ForLoop) else loop.to_values())
            for loop in loops
        ]
        return functools.reduce(operator.or_, contexts)

    def get_parameter(  # type: ignore[override]
        self, alias: str, parameter: Parameter, channel_id: int | None = None, output_id: int | None = None
    ) -> Variable:
        """Get a platform parameter.

        Appends a GetParameter operation to the active block of the experiment.

        Args:
            alias (str): The alias for the platform component.
            parameter (Parameter): The parameter to get.
            channel_id (int | None, optional): The channel of the component. Defaults to None.
            output_id (int | None, optional): The output of the component. Defaults to None.

        Returns:
            Variable: The variable the value is stored in.
        """
        base = re.sub(r"\W", "_", f"{alias}_{parameter.value}")
        base = base if re.match(r"[A-Za-z_]", base) else f"_{base}"
        existing = {variable.id for variable in self.variables}
        variable_id, suffix = base, 2
        while variable_id in existing:
            variable_id, suffix = f"{base}_{suffix}", suffix + 1
        variable = self.variable(variable_id, label=f"{parameter.value} of {alias}")
        self._append_to_active(
            GetParameter(
                variable=variable, alias=alias, parameter=parameter, channel_id=channel_id, output_id=output_id
            )
        )
        return variable

    def set_parameter(  # type: ignore[override]
        self,
        alias: str,
        parameter: Parameter,
        value: int | float | bool | Variable,
        channel_id: int | None = None,
        output_id: int | None = None,
    ) -> None:
        """Set a platform parameter.

        Appends a SetParameter operation to the active block of the experiment.

        Args:
            alias (str): The alias for the platform component.
            parameter (Parameter): The parameter to set.
            value (int | float | bool | Variable): The value to set for the parameter.
            channel_id (int | None, optional): The channel of the component. Defaults to None.
            output_id (int | None, optional): The output of the component. Defaults to None.
        """
        self._append_to_active(
            SetParameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id, output_id=output_id)
        )

    def execute_qprogram(
        self,
        qprogram: QProgram | Callable[..., QProgram],
        bus_mapping: dict[str, str] | None = None,
        debug: bool = False,
        calibration: Calibration | None = None,
    ) -> None:
        """Execute a quantum program within the experiment.

        Appends an ExecuteQProgram operation to the active block of the experiment.

        Args:
            qprogram (QProgram | Callable[..., QProgram]): The quantum program to be executed, or a function building
                it from the experiment's variables.
            bus_mapping (dict[str, str] | None, optional): Mapping of the QProgram's buses to the platform's. Defaults to
                None.
            debug (bool, optional): Whether to write the compiled program to a debug file. Defaults to False.
            calibration (Calibration | None, optional): Calibration used to compile the QProgram. Defaults to None.
        """
        self._append_to_active(
            ExecuteQProgram(qprogram=qprogram, bus_mapping=bus_mapping, calibration=calibration, debug=debug)
        )

    def set_crosstalk(self, crosstalk: CrosstalkMatrix) -> None:
        """Set the crosstalk matrix of the platform.

        Args:
            crosstalk (CrosstalkMatrix): The crosstalk matrix.
        """
        self._append_to_active(SetCrosstalk(crosstalk=crosstalk))
