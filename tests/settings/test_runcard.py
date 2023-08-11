"""Unit tests for the Runcard class."""
import ast
import re
from dataclasses import asdict

import pytest

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings import Runcard
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.typings import Parameter
from tests.data import Galadriel


@pytest.mark.parametrize("runcard_dict", [Galadriel.runcard])
class TestRuncard:
    """Unit tests for the Runcard dataclass initialization."""

    def test_attributes(self, runcard_dict):
        """Test that the attributes of the Runcard are casted into dataclasses, and that
        the values they contain are the same as the input dictionaries."""
        runcard = Runcard(**runcard_dict)

        assert isinstance(runcard.gates, runcard.GateSettings)
        assert asdict(runcard.gates) == Galadriel.gates

        assert isinstance(runcard.chip, runcard.ChipSettings)
        assert asdict(runcard.chip) == Galadriel.chip

        assert isinstance(runcard.buses, list)
        assert isinstance(runcard.buses[0], runcard.BusSettings)
        for index, bus in enumerate(runcard.buses):
            assert asdict(bus) == Galadriel.buses[index]

        assert isinstance(runcard.instruments, list)
        assert isinstance(runcard.instruments[0], dict)
        for index, instrument in enumerate(runcard.instruments):
            assert instrument == Galadriel.instruments[index]

        assert isinstance(runcard.instrument_controllers, list)
        assert isinstance(runcard.instrument_controllers[0], dict)
        for index, instrument_controller in enumerate(runcard.instrument_controllers):
            assert instrument_controller == Galadriel.instrument_controllers[index]


@pytest.mark.parametrize("gates", [Runcard(**Galadriel.runcard).gates])
class TestGateSettings:
    """Unit tests for the Runcard.GateSettings class."""

    def test_attributes(self, gates):
        """Test that the Runcard.GateSettings dataclass contains the right attributes."""
        assert isinstance(gates.name, str)
        assert isinstance(gates.delay_between_pulses, int)
        assert isinstance(gates.delay_before_readout, int)
        assert isinstance(gates.gates, dict)
        assert all(
            (isinstance(key, str), isinstance(event, GateEventSettings))
            for key, settings in gates.gates.items()
            for event in settings
        )
        assert isinstance(gates.reset_method, str)
        assert isinstance(gates.passive_reset_duration, int)
        assert isinstance(gates.operations, list)

    def test_get_operation_settings(self, gates):
        """Test the ``get_operation_settings`` method of the GateSettings class."""
        for operation in gates.operations:
            if isinstance(operation, dict):
                operation = Runcard.GateSettings.OperationSettings(**operation)
            assert isinstance(
                gates.get_operation_settings(name=operation.name),
                gates.OperationSettings,
            )

    def test_get_operation_settings_raises_error_when_operation_does_not_exist(self, gates):
        """Test the ``get_gate`` method of the GateSettings class."""
        name = "unkown_operation"
        with pytest.raises(ValueError, match=f"Operation {name} not found in gates."):
            gates.get_operation_settings(name)

    def test_get_gate(self, gates):
        """Test the ``get_gate`` method of the GateSettings class."""
        gates_qubits = [
            (re.search(GATE_ALIAS_REGEX, alias)["gate"], re.search(GATE_ALIAS_REGEX, alias)["qubits"])
            for alias in gates.gates.keys()
        ]
        assert all(
            isinstance(gate_event, GateEventSettings)
            for gate_name, gate_qubits in gates_qubits
            for gate_event in gates.get_gate(name=gate_name, qubits=ast.literal_eval(gate_qubits))
        )

    def test_get_gate_raises_error(self, gates):
        """Test that the ``get_gate`` method raises an error when the name is not found."""
        name = "test"
        qubits = 0

        error_string = re.escape(f"Gate {name} for qubits {qubits} not found in settings").replace(
            "\\", ""
        )  # fixes re.escape bug
        with pytest.raises(KeyError, match=error_string):
            gates.get_gate(name, qubits=qubits)

    def test_gate_names(self, gates):
        """Test the ``gate_names`` method of the GateSettings class."""
        expected_names = list(gates.gates.keys())
        assert gates.gate_names == expected_names

    def test_set_platform_parameters(self, gates):
        """Test that with ``set_parameter`` we can change all settings of the platform."""
        gates.set_parameter(parameter=Parameter.DELAY_BEFORE_READOUT, value=1234)
        assert gates.delay_before_readout == 1234

        gates.set_parameter(parameter=Parameter.DELAY_BETWEEN_PULSES, value=1234)
        assert gates.delay_between_pulses == 1234

    @pytest.mark.parametrize("alias", ["X(0)", "M(0)"])
    def test_set_gate_parameters(self, alias: str, gates):
        """Test that with ``set_parameter`` we can change all settings of the platform's gates."""
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        assert regex_match is not None

        name = regex_match["gate"]
        qubits_str = regex_match["qubits"]
        qubits = ast.literal_eval(qubits_str)

        gates.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
        assert gates.get_gate(name=name, qubits=qubits)[0].pulse.duration == 1234

        gates.set_parameter(alias=alias, parameter=Parameter.PHASE, value=1234)
        assert gates.get_gate(name=name, qubits=qubits)[0].pulse.phase == 1234

        gates.set_parameter(alias=alias, parameter=Parameter.AMPLITUDE, value=1234)
        assert gates.get_gate(name=name, qubits=qubits)[0].pulse.amplitude == 1234

    @pytest.mark.parametrize("alias", ["X(0,)", "X()", "X", ""])
    def test_set_gate_parameters_raises_error_when_alias_has_incorrect_format(self, alias: str, gates):
        """Test that with ``set_parameter`` will raise error when alias has incorrect format"""
        with pytest.raises(ValueError, match=re.escape(f"Alias {alias} has incorrect format")):
            gates.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
