import ast
import re
from dataclasses import asdict, dataclass

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings.circuit_compilation.bus_settings import BusSettings
from qililab.settings.circuit_compilation.gate_event_settings import GateEventSettings
from qililab.settings.settings import Settings
from qililab.typings.enums import Parameter


@dataclass
class GatesSettings(Settings):
    """Dataclass with all the settings and gates definitions needed to decompose gates into pulses."""

    minimum_clock_time: int
    delay_before_readout: int
    gates: dict[str, list[GateEventSettings]]
    buses: dict[str, BusSettings]

    def __post_init__(self):
        """Build the Gates Settings based on the master settings."""
        self.gates = {gate: [GateEventSettings(**event) for event in schedule] for gate, schedule in self.gates.items()}
        self.buses = {bus: BusSettings(**settings) for bus, settings in self.buses.items()}

    def to_dict(self):
        """Serializes gate settings to dictionary and removes fields with None values"""

        def remove_none_values(data):
            if isinstance(data, dict):
                data = {key: remove_none_values(item) for key, item in data.items() if item is not None}
            elif isinstance(data, list):
                data = [remove_none_values(item) for item in data if item is not None]
            return data

        return remove_none_values(data=asdict(self))

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
        channel_id: int | str | None = None,
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
        if parameter == Parameter.DELAY:
            if alias not in self.buses:
                raise ValueError(f"Could not find bus {alias} in gate settings.")
            self.buses[alias].delay = int(value)
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
        channel_id: int | str | None = None,
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
        if parameter == Parameter.DELAY:
            if alias not in self.buses:
                raise ValueError(f"Could not find bus {alias} in gate settings.")
            return self.buses[alias].delay
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        if regex_match is None:
            raise ValueError(f"Could not find gate {alias} in gate settings.")
        name = regex_match["gate"]
        qubits_str = regex_match["qubits"]
        qubits = ast.literal_eval(qubits_str)
        gates_settings = self.get_gate(name=name, qubits=qubits)
        schedule_element = 0 if len(alias.split("_")) == 1 else int(alias.split("_")[1])
        return gates_settings[schedule_element].get_parameter(parameter)