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

import ast
import re

from pydantic import BaseModel

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings.digital.gate_event import GateEvent
from qililab.typings import ChannelID, Parameter, ParameterValue


class DigitalCompilationSettings(BaseModel):
    """Dataclass with all the settings and gates definitions needed to decompose gates into pulses."""

    topology: list[tuple[int, int]]
    gates: dict[str, list[GateEvent]]
    relaxation_duration: int = 200_000

    def to_dict(self):
        """Serializes gate settings to dictionary and removes fields with None values"""

        return self.model_dump()

    def get_gate(self, name: str, qubits: int | tuple[int, int] | tuple[int]) -> list[GateEvent]:
        """Get gates settings from runcard for a given gate name and qubits.

        Args:
            name (str): Name of the gate.
            qubits (int |  tuple[int, int] | tuple[int]): The qubits the gate is acting on.

        Raises:
            ValueError: If no gate is found.

        Returns:
            GatesSettings: gate settings.
        """

        gate_qubits = (
            (qubits,) if isinstance(qubits, int) else qubits
        )  # tuplify so that the join method below is general
        gate_name = f"{name}({', '.join(map(str, gate_qubits))})"
        gate_name_t = f"{name}({', '.join(map(str, gate_qubits[::-1]))})"

        # parse spaces in tuple if needed, check first case with spaces since it is more common
        if gate_name.replace(" ", "") in self.gates.keys():
            return self.gates[gate_name.replace(" ", "")]
        if gate_name in self.gates.keys():
            return self.gates[gate_name]
        if gate_name_t.replace(" ", "") in self.gates.keys():
            return self.gates[gate_name_t.replace(" ", "")]
        if gate_name_t in self.gates.keys():
            return self.gates[gate_name_t]
        raise KeyError(f"Gate {name} for qubits {qubits} not found in settings.")

    @property
    def gate_names(self) -> list[str]:
        """GatesSettings 'gate_names' property.

        Returns:
            list[str]: List of the names of all the defined gates.
        """
        return list(self.gates.keys())

    def set_parameter(
        self, alias: str, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None
    ):
        """Cast the new value to its corresponding type and set the new attribute.

        Args:
            parameter (Parameter): Name of the parameter to get.
            value (float | str | bool): New value to set in the parameter.
            channel_id (int, optional): Channel id. Defaults to None.
            alias (str): String which specifies where the parameter can be found.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if regex_match is None:
            raise ValueError(f"Alias {alias} has incorrect format")
        name = regex_match["gate"]
        qubits_str = regex_match["qubits"]
        qubits = ast.literal_eval(qubits_str)
        gates_settings = self.get_gate(name=name, qubits=qubits)
        schedule_element = 0 if len(alias.split("_")) == 1 else int(alias.split("_")[1])
        gates_settings[schedule_element].set_parameter(parameter, value)

    def get_parameter(self, alias: str, parameter: Parameter, channel_id: int | str | None = None):
        """Get parameter from gate settings.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int, optional): Channel id. Defaults to None.
            alias (str): String which specifies where the parameter can be found.
        """
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if regex_match is None:
            raise ValueError(f"Could not find gate {alias} in gate settings.")
        name = regex_match["gate"]
        qubits_str = regex_match["qubits"]
        qubits = ast.literal_eval(qubits_str)
        gates_settings = self.get_gate(name=name, qubits=qubits)
        schedule_element = 0 if len(alias.split("_")) == 1 else int(alias.split("_")[1])
        return gates_settings[schedule_element].get_parameter(parameter)
