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
import warnings
from types import MappingProxyType
from typing import Callable

import numpy as np

from qililab.qprogram.calibration import Calibration
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.operations import ExecuteQProgram, GetParameter, SetParameter
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.structured_program import StructuredProgram
from qililab.qprogram.variable import Domain, Variable
from qililab.typings.enums import Parameter
from qililab.yaml import yaml


@yaml.register_class
class Experiment(StructuredProgram):
    """Represents an experiment.

    This class allows setting platform parameters and executing quantum programs.
    """

    _domain_of_parameter: MappingProxyType[Parameter, Domain] = MappingProxyType(
        {
            Parameter.AMPLITUDE: Domain.Voltage,
            Parameter.GAIN: Domain.Voltage,
            Parameter.GAIN_I: Domain.Voltage,
            Parameter.GAIN_Q: Domain.Voltage,
            Parameter.DC_OFFSET: Domain.Voltage,
            Parameter.OFFSET_I: Domain.Voltage,
            Parameter.OFFSET_Q: Domain.Voltage,
            Parameter.OFFSET_OUT0: Domain.Voltage,
            Parameter.OFFSET_OUT1: Domain.Voltage,
            Parameter.OFFSET_OUT2: Domain.Voltage,
            Parameter.OFFSET_OUT3: Domain.Voltage,
            Parameter.FLUX: Domain.Flux,
            Parameter.DURATION: Domain.Time,
            Parameter.LO_FREQUENCY: Domain.Frequency,
            Parameter.IF: Domain.Frequency,
            Parameter.PHASE: Domain.Phase,
            Parameter.DRAG_COEFFICIENT: Domain.Scalar,
            Parameter.THRESHOLD: Domain.Scalar,
            Parameter.THRESHOLD_ROTATION: Domain.Scalar,
        }
    )

    _type_of_parameter: MappingProxyType[Parameter, type] = MappingProxyType(
        {Parameter.DRAG_COEFFICIENT: float, Parameter.THRESHOLD: float, Parameter.THRESHOLD_ROTATION: float}
    )

    def __init__(self, label: str, calibration: Calibration | None = None) -> None:
        super().__init__()

        self.label: str = label
        self.calibration: Calibration | None = calibration
        self.crosstalk_data: CrosstalkMatrix | None = None
        self.value_flux_list: dict = {}
        if self.calibration:
            self.crosstalk_data = self.calibration.crosstalk_matrix

    def get_parameter(self, alias: str, parameter: Parameter, channel_id: int | None = None):
        """Set a platform parameter.

        Appends a SetParameter operation to the active block of the experiment.

        Args:
            alias (str): The alias for the platform component.
            parameter (Parameter): The parameter to set.
            value (int | float): The value to set for the parameter.
        """
        variable = self.variable(
            label=f"{parameter.value} of {alias}",
            domain=self._domain_of_parameter.get(parameter, Domain.Scalar),
            type=self._type_of_parameter.get(parameter, None),
        )
        operation = GetParameter(variable=variable, alias=alias, parameter=parameter, channel_id=channel_id)
        self._active_block.append(operation)
        return variable

    def set_parameter(
        self,
        alias: str,
        parameter: Parameter,
        value: int | float | Variable,
        channel_id: int | None = None,
        flux_list: list[str] | None = None,
    ):
        """Set a platform parameter.

        Appends a SetParameter operation to the active block of the experiment.

        Args:
            alias (str): The alias for the platform component.
            parameter (Parameter): The parameter to set.
            value (int | float): The value to set for the parameter.
        """
        if parameter == Parameter.FLUX:
            if not self.get_crosstalk and not self.crosstalk_data:
                if not flux_list:
                    flux_list = [alias]
                self.crosstalk_data = CrosstalkMatrix.from_array(flux_list, np.eye(len(flux_list)))
                warnings.warn(f"Crosstalk not given, using identity as crosstalk\n{self.crosstalk_data}")
            elif self.get_crosstalk:
                self.crosstalk_data = self.get_crosstalk
            if alias not in self.crosstalk_data.matrix.keys():  # type: ignore[union-attr]
                for key in list(self.crosstalk_data.matrix.keys()):  # type: ignore[union-attr]
                    self.crosstalk_data[alias] = {key: 0.0}  # type: ignore[index]
                    self.crosstalk_data[key] = {alias: 0.0}  # type: ignore[index]
                self.crosstalk_data[alias] = {alias: 1.0}  # type: ignore[index]
                warnings.warn(
                    f"{alias} not inside crosstalk matrix, adding it with identity values\n{self.crosstalk_data}"
                )
            if isinstance(value, Variable):
                self.value_flux_list[value.label] = alias

        operation = SetParameter(alias=alias, parameter=parameter, value=value, channel_id=channel_id)
        self._active_block.append(operation)

    def execute_qprogram(
        self,
        qprogram: QProgram | Callable[..., QProgram],  # type: ignore
        bus_mapping: dict[str, str] | None = None,
        debug: bool = False,
    ):
        """Execute a quantum program within the experiment.

        Appends an ExecuteQProgram operation to the active block of the experiment.

        Args:
            qprogram (QProgram): The quantum program to be executed.
        """
        operation = ExecuteQProgram(
            qprogram=qprogram, bus_mapping=bus_mapping, calibration=self.calibration, debug=debug
        )
        self._active_block.append(operation)
