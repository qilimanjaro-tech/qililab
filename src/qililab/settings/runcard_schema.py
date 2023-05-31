"""PlatformSchema class."""
import ast
import re
from dataclasses import dataclass
from typing import Literal

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings.ddbb_element import DDBBElement
from qililab.typings.enums import Category, OperationTimingsCalculationMethod, Parameter, ResetMethod
from qililab.utils import nested_dataclass


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
                phase: float
                parameters: dict

            name: str
            pulse: PulseSettings

            def set_parameter(self, parameter: Parameter, value: float | str | bool):
                """Change an operation parameter with the given value."""
                if not hasattr(self.pulse, parameter.value):
                    self.pulse.parameters[parameter.value] = value
                setattr(self.pulse, parameter.value, value)

        @dataclass
        class GateSettings:
            """GatesSchema class."""

            name: str
            amplitude: float
            phase: float
            duration: int
            shape: dict

            def set_parameter(self, parameter: Parameter, value: float | str | bool):
                """Change a gate parameter with the given value."""
                param = parameter.value
                if not hasattr(self, param):
                    self.shape[param] = value
                else:
                    setattr(self, param, value)

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
        gates: dict[int | tuple[int, int], list[GateSettings]]

        def __post_init__(self):
            """build the Gate Settings based on the master settings"""
            self.operations = (
                [self.OperationSettings(**operation) for operation in self.operations]
                if self.operations is not None
                else None
            )
            self.gates = (
                {qubit: [self.GateSettings(**gate) for gate in gate_list] for qubit, gate_list in self.gates.items()}
                if self.gates is not None
                else None
            )

        def get_operation_settings(self, name: str) -> OperationSettings | None:
            """Get OperationSettings by operation's name

            Args:
                name (str): Name of the operation

            Returns:
                OperationSettings: Operation's settings
            """
            for operation in self.operations:
                if operation.name == name:
                    return operation
            return None

        def get_gate(self, name: str, qubits: int | tuple[int, int]):
            """Get gate with the given name for the given qubit(s).

            Args:
                name (str): Name of the gate.
                qubits (int |  tuple[int, int]): The qubits the gate is acting on.

            Raises:
                ValueError: If no gate is found.

            Returns:
                GateSettings: GateSettings class or None.
            """
            if qubits in self.gates:
                for gate in self.gates[qubits]:
                    if gate.name == name:
                        return gate
            raise ValueError(f"Gate {name} for qubits {qubits} not found in settings.")

        @property
        def gate_names(self) -> list[str]:
            """PlatformSettings 'gate_names' property.

            Returns:
                list[str]: List of the names of all the defined gates.
            """
            return list({gate.name for gates in self.gates.values() for gate in gates})

        @property
        def operation_names(self) -> list[str]:
            """Get the names of all operations in the PlatformSettings

            Returns:
                List[str]: List of all operation names
            """
            return [operation.name for operation in self.operations]

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
            operation_settings = self.get_operation_settings(name=alias)
            if operation_settings is not None:
                operation_settings.set_parameter(parameter=parameter, value=value)
                return
            regex_match = re.search(GATE_ALIAS_REGEX, alias)
            if regex_match is None:
                raise ValueError(f"Alias {alias} has incorrect format")
            name = regex_match["gate"]
            qubits_str = regex_match["qubits"]
            qubits = ast.literal_eval(qubits_str)
            gate_settings = self.get_gate(name=name, qubits=qubits)
            gate_settings.set_parameter(parameter, value)

    settings: PlatformSettings
    schema: Schema
