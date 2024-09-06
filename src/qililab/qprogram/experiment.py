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

from qililab.qprogram.calibration import Calibration
from qililab.qprogram.operations import ExecuteQProgram, SetParameter
from qililab.qprogram.qprogram import QProgram
from qililab.qprogram.structured_program import StructuredProgram
from qililab.typings.enums import Parameter
from qililab.yaml import yaml


@yaml.register_class
class Experiment(StructuredProgram):
    """Represents an experiment.

    This class allows setting platform parameters and executing quantum programs.
    """

    def set_parameter(self, alias: str, parameter: Parameter, value: int | float | int):
        """Set a platform parameter.

        Appends a SetParameter operation to the active block of the experiment.

        Args:
            alias (str): The alias for the platform component.
            parameter (Parameter): The parameter to set.
            value (int | float): The value to set for the parameter.
        """
        operation = SetParameter(alias=alias, parameter=parameter, value=value)
        self._active_block.append(operation)

    def execute_qprogram(
        self,
        qprogram: QProgram,
        bus_mapping: dict[str, str] | None = None,
        calibration: Calibration | None = None,
        debug: bool = False,
    ):
        """Execute a quantum program within the experiment.

        Appends an ExecuteQProgram operation to the active block of the experiment.

        Args:
            qprogram (QProgram): The quantum program to be executed.
        """
        operation = ExecuteQProgram(qprogram=qprogram, bus_mapping=bus_mapping, calibration=calibration, debug=debug)
        self._active_block.append(operation)
