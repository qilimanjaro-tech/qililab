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

"""Runcard class."""
import ast
import re
from dataclasses import asdict, dataclass
from typing import Literal

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.typings.enums import OperationTimingsCalculationMethod, Parameter, ResetMethod
from qililab.utils import nested_dataclass

from .settings import Settings

# pylint: disable=too-few-public-methods


@nested_dataclass
class Runcard:
    """Runcard class. Casts the platform dictionary into a class.

    The input to the constructor should be a dictionary of the desired runcard with the following structure:
    - gates_settings:
    - chip:
    - buses:
    - instruments: List of "instruments" dictionaries
    - instrument_controllers: List of "instrument_controllers" dictionaries

    The gates_settings, chip and bus dictionaries will be passed to their corresponding Runcard.GatesSettings,
    Runcard.Chip or Runcard.Bus classes here, meanwhile the instruments and instrument_controllers will remain dictionaries.

    Then this full class gets passed to the Platform who will instantiate the actual qililab Chip, Buses/Bus and the
    corresponding Instrument classes with the settings attributes of this class.

    Args:
        gates_settings (dict): Gates settings dictionary -> Runcard.GatesSettings inner dataclass
        chip (dict): Chip settings dictionary -> Runcard.Chip settings inner dataclass
        buses (list[dict]): List of Bus settings dictionaries -> list[Runcard.Bus] settings inner dataclass
        instruments (list[dict]): List of dictionaries containing the "instruments" information (does not transform)
        instruments_controllers (list[dict]): List of dictionaries containing the "instrument_controllers" information
            (does not transform)
    """

    # Inner dataclasses definition
    @dataclass
    class Bus:
        """Dataclass with all the settings the buses of the platform need.

        Args:
            alias (str): Alias of the bus.
            system_control (dict): Dictionary containing the settings of the system control of the bus.
            port (str): Alias of the port of the chip the bus is connected to.
            distortions (list[dict]): List of dictionaries containing the settings of the distortions applied to each
                bus.
            delay (int, optional): Delay applied to all pulses sent in this bus. Defaults to 0.
        """

        alias: str
        system_control: dict
        port: str
        distortions: list[dict]
        delay: int = 0

    @dataclass
    class Chip:
        """Dataclass with all the settings/nodes the chip of the platform needs.

        Args:
            nodes (list[dict]): List of dictionaries containing the settings of all the nodes of the chip.
        """

        nodes: list[dict]

    @nested_dataclass
    class GatesSettings(Settings):
        """Dataclass with all the settings and gates definitions needed to decompose gates into pulses."""

        @nested_dataclass
        class OperationSettings:
            """Dataclass with all the settings an operation needs."""

            @dataclass
            class PulseSettings:
                """Dataclass with all the settings a pulse needs."""

                name: str
                amplitude: float
                duration: int
                parameters: dict

            name: str
            pulse: PulseSettings

        minimum_clock_time: int
        delay_between_pulses: int
        delay_before_readout: int
        timings_calculation_method: Literal[
            OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE, OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE
        ]
        reset_method: Literal[ResetMethod.ACTIVE, ResetMethod.PASSIVE]
        passive_reset_duration: int
        operations: list[OperationSettings]
        gates: dict[str, list[GateEventSettings]]

        def __post_init__(self):
            """Build the Gates Settings based on the master settings."""
            self.gates = {
                gate: [GateEventSettings(**event) for event in schedule] for gate, schedule in self.gates.items()
            }

        def to_dict(self):
            """Serializes gate settings to dictionary and removes fields with None values"""

            def remove_none_values(data):
                if isinstance(data, dict):
                    data = {key: remove_none_values(item) for key, item in data.items() if item is not None}
                elif isinstance(data, list):
                    data = [remove_none_values(item) for item in data if item is not None]
                return data

            return remove_none_values(data=asdict(self))

        def get_operation_settings(self, name: str) -> OperationSettings:
            """Get OperationSettings by operation's name.

            Args:
                name (str): Name of the operation

            Raises:
                ValueError: If no operation is found

            Returns:
                OperationSettings: Operation's settings
            """
            for operation in self.operations:
                # TODO: Fix bug that parses settings as dict instead of defined classes
                if isinstance(operation, dict):
                    operation = Runcard.GatesSettings.OperationSettings(**operation)
                if operation.name == name:
                    return operation
            raise ValueError(f"Operation {name} not found in gates settings.")

        def get_gate(self, name: str, qubits: int | tuple[int, int] | tuple[int]):
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
            self,
            parameter: Parameter,
            value: float | str | bool,
            channel_id: int | None = None,
            alias: str | None = None,
        ):
            """Cast the new value to its corresponding type and set the new attribute.

            Args:
                parameter (Parameter): Name of the parameter to get.
                value (float | str | bool): New value to set in the parameter.
                channel_id (int | None, optional): Channel id. Defaults to None.
                alias (str): String which specifies where the parameter can be found.
            """
            if alias is None or alias == "platform":
                super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)
                return
            regex_match = re.search(GATE_ALIAS_REGEX, alias)
            if regex_match is None:
                raise ValueError(f"Alias {alias} has incorrect format")
            name = regex_match["gate"]
            qubits_str = regex_match["qubits"]
            qubits = ast.literal_eval(qubits_str)
            gates_settings = self.get_gate(name=name, qubits=qubits)
            schedule_element = 0 if len(alias.split("_")) == 1 else int(alias.split("_")[1])
            gates_settings[schedule_element].set_parameter(parameter, value)

        def get_parameter(
            self,
            parameter: Parameter,
            channel_id: int | None = None,
            alias: str | None = None,
        ):
            """Get parameter from gate settings.

            Args:
                parameter (Parameter): Name of the parameter to get.
                channel_id (int | None, optional): Channel id. Defaults to None.
                alias (str): String which specifies where the parameter can be found.
            """
            if alias is None or alias == "platform":
                return super().get_parameter(parameter=parameter, channel_id=channel_id)
            regex_match = re.search(GATE_ALIAS_REGEX, alias)
            if regex_match is None:
                raise ValueError(f"Could not find gate {alias} in gate settings.")
            name = regex_match["gate"]
            qubits_str = regex_match["qubits"]
            qubits = ast.literal_eval(qubits_str)
            gates_settings = self.get_gate(name=name, qubits=qubits)
            schedule_element = 0 if len(alias.split("_")) == 1 else int(alias.split("_")[1])
            return gates_settings[schedule_element].get_parameter(parameter)

    # Runcard class actual initialization
    name: str
    device_id: int
    chip: Chip
    buses: list[Bus]  # This actually is a list[dict] until the post_init is called
    instruments: list[dict]
    instrument_controllers: list[dict]
    gates_settings: GatesSettings

    def __post_init__(self):
        self.buses = [self.Bus(**bus) for bus in self.buses] if self.buses is not None else None
