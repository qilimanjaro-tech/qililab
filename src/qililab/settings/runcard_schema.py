"""PlatformSchema class."""
import ast
import re
from dataclasses import dataclass
from typing import Literal

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings.ddbb_element import DDBBElement
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.typings.enums import Category, OperationTimingsCalculationMethod, Parameter, ResetMethod
from qililab.utils import nested_dataclass

# pylint: disable=too-few-public-methods


@nested_dataclass
class RuncardSchema:
    """PlatformSchema class. Casts the platform dictionary into a class.
    The input to the constructor should be a dictionary with the following structure:

    - platform: settings dictionary.
    - schema: schema dictionary:
        - buses: buses dictionary:
            - elements: list of bus dictionaries with the following structure:
                - name: "readout" or "control"
                - awg: settings dictionary.
                - signal_generator: settings dictionary.
                - qubit / resonator: settings dictionary.
    """

    @nested_dataclass
    class Schema:
        """SchemaDict class."""

        @dataclass
        class BusSchema:
            """Bus schema class."""

            id_: int
            category: str
            system_control: dict
            port: int
            distortions: list[dict]
            alias: str | None = None
            delay: int = 0

        @dataclass
        class ChipSchema:
            """Chip schema class."""

            id_: int
            category: str
            nodes: list[dict]
            alias: str | None = None

        chip: ChipSchema | None
        buses: list[BusSchema]
        instruments: list[dict]
        instrument_controllers: list[dict]

        def __post_init__(self):
            self.buses = [self.BusSchema(**bus) for bus in self.buses] if self.buses is not None else None
            if isinstance(self.chip, dict):
                self.chip = self.ChipSchema(**self.chip)  # pylint: disable=not-a-mapping

    @nested_dataclass
    class PlatformSettings(DDBBElement):
        """SettingsSchema class."""

        @nested_dataclass
        class OperationSettings:
            """OperationSchema class"""

            @dataclass
            class PulseSettings:
                """PulseSchema class"""

                name: str
                amplitude: float
                duration: int
                parameters: dict

            name: str
            pulse: PulseSettings

        name: str
        device_id: int
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
            """build the GatesSettings based on the master settings"""

            self.gates = {
                gate: [GateEventSettings(**event) for event in schedule] for gate, schedule in self.gates.items()
            }

        def get_operation_settings(self, name: str) -> OperationSettings:
            """Get OperationSettings by operation's name

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
                    operation = RuncardSchema.PlatformSettings.OperationSettings(**operation)
                if operation.name == name:
                    return operation
            raise ValueError(f"Operation {name} not found in platform settings.")

        def get_gate(self, name: str, qubits: int | tuple[int, int] | tuple[int]):
            """Get gates settings from runcard for a given gate name and qubits.

            Args:
                name (str): Name of the gate.
                qubits (int |  tuple[int, int] | tuple[int]): The qubits the gate is acting on.

            Raises:
                ValueError: If no gate is found.

            Returns:
                GateSettings: gates settings.
            """

            gate_qubits = (
                (qubits,) if isinstance(qubits, int) else qubits
            )  # tuplify so that the join method below is general
            gate_name = f"{name}({', '.join(map(str, gate_qubits))})"

            # parse spaces in tuple if needed, check first case with spaces since it is more common
            if gate_name.replace(" ", "") in self.gates.keys():
                return self.gates[gate_name.replace(" ", "")]
            if gate_name in self.gates.keys():
                return self.gates[gate_name]
            raise KeyError(f"Gate {name} for qubits {qubits} not found in settings.")

        @property
        def gate_names(self) -> list[str]:
            """PlatformSettings 'gate_names' property.

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
            """Cast the new value to its corresponding type and set the new attribute."""
            if alias is None or alias == Category.PLATFORM.value:
                super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)
                return
            regex_match = re.search(GATE_ALIAS_REGEX, alias)
            if regex_match is None:
                raise ValueError(f"Alias {alias} has incorrect format")
            name = regex_match["gate"]
            qubits_str = regex_match["qubits"]
            qubits = ast.literal_eval(qubits_str)
            gates = self.get_gate(name=name, qubits=qubits)
            schedule_element = 0 if len(alias.split("_")) == 1 else int(alias.split("_")[1])
            gates[schedule_element].set_parameter(parameter, value)

    settings: PlatformSettings
    schema: Schema
