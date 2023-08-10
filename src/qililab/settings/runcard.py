"""Runcard class."""
import ast
import re
from dataclasses import dataclass
from typing import Literal

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings.ddbb_element import DDBBElement
from qililab.typings.enums import Category, OperationTimingsCalculationMethod, Parameter, ResetMethod
from qililab.utils import nested_dataclass

# pylint: disable=too-few-public-methods


@nested_dataclass
class Runcard:
    """Runcard class. Casts the platform dictionary into a class.

    The input to the constructor should be a dictionary of the desired runcard with the following structure:

    - transpilation_settings:
    - chip:
    - buses:
    - instruments: List of "instruments" dictionaries
    - instrument_controllers: List of "instrument_controllers" dictionaries

    The transpilation_settings, chip and bus dictionaries will be passed to their corresponding TranpilationSettings,
    ChipSettings or BusSettings here, meanwhile the instruments and instrument_controllers will remain dictionaries.

    Then this full class gets passed to the Platform who will instantiate the actual qililab Chip, Buses/Bus and the
    corresponding Instrument classes with the settings attributes of this class.

    Args:
        transpilation_settings (dict): TranspilationSettings dictionary -> TranspilationSettings
        chip (dict): ChipSettings dictionary -> ChipSettings
        buses (list[dict]): List of BusSettings dictionaries -> list[BusSettings]
        instruments (list[dict]): List of dictionaries containing the "instruments" information
        instruments_controllers (list[dict]): List of dictionaries containing the "instrument_controllers" information

    Attributes:
        transpilation_settings (TranspilationSettings: Transformed transpilation settings dictionary
        chip (ChipSettings): Transformed chip settings dictionary
        buses (list[BusSettings]): Transformed buses settings list of dictionaries
        instruments (list[dict]): Same instrument list of dictionaries (not transformed)
        instruments_controllers (list[dict]): Same instrument_controllers list of dictionaries (not transformed)
    """

    # Inner dataclasses definition
    @dataclass
    class BusSettings:
        """Bus settings class."""

        id_: int
        category: str
        system_control: dict
        port: int
        distortions: list[dict]
        alias: str | None = None
        delay: int = 0

    @dataclass
    class ChipSettings:
        """Chip settings class."""

        id_: int
        category: str
        nodes: list[dict]
        alias: str | None = None

    @nested_dataclass
    class TranspilationSettings(DDBBElement):
        """TranspilationSettings class."""

        @nested_dataclass
        class OperationSettings:
            """OperationSettings class"""

            @dataclass
            class PulseSettings:
                """PulseSettings class"""

                name: str
                amplitude: float
                duration: int
                parameters: dict

            name: str
            pulse: PulseSettings

        @dataclass
        class GateSettings:
            """GatesSettings class."""

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
            self.gates = (
                {qubit: [self.GateSettings(**gate) for gate in gate_list] for qubit, gate_list in self.gates.items()}
                if self.gates is not None
                else None
            )

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
                    operation = Runcard.TranspilationSettings.OperationSettings(**operation)
                if operation.name == name:
                    return operation
            raise ValueError(f"Operation {name} not found in platform settings.")

        def get_gate(self, name: str, qubits: int | tuple[int, int]):
            """Get gate with the given name for the given qubit(s).

            Args:
                name (str): Name of the gate.
                qubits (int |  tuple[int, int]): The qubits the gate is acting on.

            Raises:
                ValueError: If no gate is found.

            Returns:
                GateSettings: GateSettings class.
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
            gate_settings = self.get_gate(name=name, qubits=qubits)
            gate_settings.set_parameter(parameter, value)

    # Runcard class actual initialization
    chip: ChipSettings
    buses: list[BusSettings]
    instruments: list[dict]
    instrument_controllers: list[dict]
    transpilation_settings: TranspilationSettings

    def __post_init__(self):
        self.buses = [self.BusSettings(**bus) for bus in self.buses] if self.buses is not None else None
        if isinstance(self.chip, dict):
            self.chip = self.ChipSettings(**self.chip)  # pylint: disable=not-a-mapping
