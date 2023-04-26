"""PlatformSchema class."""
from dataclasses import dataclass
from typing import List, Literal

from qililab.circuit.operations.special_operations.reset import Reset
from qililab.constants import PLATFORM
from qililab.settings.ddbb_element import DDBBElement
from qililab.typings.enums import (
    Category,
    MasterGateSettingsName,
    OperationTimingsCalculationMethod,
    Parameter,
    ResetMethod,
)
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
            alias: str | None = None

        @dataclass
        class ChipSchema:
            """Chip schema class."""

            id_: int
            category: str
            nodes: List[dict]
            alias: str | None = None

        chip: ChipSchema | None
        buses: List[BusSchema]
        instruments: List[dict]
        instrument_controllers: List[dict]

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
                frequency: float
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
            amplitude: float | Literal[MasterGateSettingsName.MASTER_AMPLITUDE_GATE]
            phase: float
            duration: int | Literal[MasterGateSettingsName.MASTER_DURATION_GATE]
            shape: dict

            def __post_init__(self):
                """build the Gate Settings based on the master settings"""
                self.amplitude = self._convert_string_to_master_gate_settings_enum(gate_current_value=self.amplitude)
                self.duration = self._convert_string_to_master_gate_settings_enum(gate_current_value=self.duration)

            def _convert_string_to_master_gate_settings_enum(self, gate_current_value: int | float | str):
                """convert string to master gate settings enum when value is depending on masters value"""
                if not isinstance(gate_current_value, str):
                    return gate_current_value
                if gate_current_value not in [PLATFORM.MASTER_AMPLITUDE_GATE, PLATFORM.MASTER_DURATION_GATE]:
                    raise ValueError(
                        f"Master Name {gate_current_value} not supported. The only supported names are: "
                        + f"[{PLATFORM.MASTER_AMPLITUDE_GATE}, {PLATFORM.MASTER_DURATION_GATE}]"
                    )
                if gate_current_value == PLATFORM.MASTER_AMPLITUDE_GATE:
                    return MasterGateSettingsName.MASTER_AMPLITUDE_GATE
                return MasterGateSettingsName.MASTER_DURATION_GATE

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
        master_amplitude_gate: float
        master_duration_gate: int
        timings_calculation_method: Literal[
            OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE, OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE
        ]
        reset_method: Literal[ResetMethod.ACTIVE, ResetMethod.PASSIVE]
        passive_reset_duration: int
        operations: List[OperationSettings]
        gates: List[GateSettings]

        def __post_init__(self):
            """build the Gate Settings based on the master settings"""
            self.gates = [self.GateSettings(**gate) for gate in self.gates] if self.gates is not None else None
            self.operations = (
                [self.OperationSettings(**operation) for operation in self.operations]
                if self.operations is not None
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

        def get_gate(self, name: str) -> GateSettings | None:
            """Get gate with the given name.
            Args:
                name (str): Name of the gate.
            Returns:
                GateSettings: GateSettings class or None.
            """
            for gate in self.gates:
                if gate.name == name:
                    return gate
            return None

        @property
        def gate_names(self) -> List[str]:
            """PlatformSettings 'gate_names' property.
            Returns:
                List[str]: List of the names of all the defined gates.
            """
            return [gate.name for gate in self.gates]

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
            gate_settings = self.get_gate(name=alias)
            if gate_settings is not None:
                gate_settings.set_parameter(parameter=parameter, value=value)
            operation_settings = self.get_operation_settings(name=alias)
            if operation_settings is not None:
                operation_settings.set_parameter(parameter=parameter, value=value)

    settings: PlatformSettings
    schema: Schema
