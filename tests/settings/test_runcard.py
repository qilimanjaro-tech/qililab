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

        assert isinstance(runcard.name, str)
        assert runcard.name == Galadriel.runcard["name"]

        assert isinstance(runcard.device_id, int)
        assert runcard.device_id == Galadriel.runcard["device_id"]

        assert isinstance(runcard.gates_settings, runcard.GatesSettings)
        assert asdict(runcard.gates_settings) == Galadriel.runcard["gates_settings"]

        assert isinstance(runcard.chip, runcard.ChipSettings)
        assert asdict(runcard.chip) == Galadriel.runcard["chip"]

        assert isinstance(runcard.buses, list)
        assert isinstance(runcard.buses[0], runcard.BusSettings)
        for index, bus in enumerate(runcard.buses):
            assert asdict(bus) == Galadriel.runcard["buses"][index]

        assert isinstance(runcard.instruments, list)
        assert isinstance(runcard.instruments[0], dict)
        for index, instrument in enumerate(runcard.instruments):
            assert instrument == Galadriel.runcard["instruments"][index]

        assert isinstance(runcard.instrument_controllers, list)
        assert isinstance(runcard.instrument_controllers[0], dict)
        for index, instrument_controller in enumerate(runcard.instrument_controllers):
            assert instrument_controller == Galadriel.runcard["instrument_controllers"][index]


@pytest.mark.parametrize("gates_settings", [Runcard(**Galadriel.runcard).gates_settings])
class TestGateSettings:
    """Unit tests for the Runcard.GateSettings class."""

    def test_attributes(self, gates_settings):
        """Test that the Runcard.GateSettings dataclass contains the right attributes."""
        assert isinstance(gates_settings.delay_between_pulses, int)
        assert isinstance(gates_settings.delay_before_readout, int)
        assert isinstance(gates_settings.gates, dict)
        assert all(
            (isinstance(key, str), isinstance(event, GateEventSettings))
            for key, settings in gates_settings.gates.items()
            for event in settings
        )
        assert isinstance(gates_settings.reset_method, str)
        assert isinstance(gates_settings.passive_reset_duration, int)
        assert isinstance(gates_settings.operations, list)

    def test_get_operation_settings(self, gates_settings):
        """Test the ``get_operation_settings`` method of the GateSettings class."""
        for operation in gates_settings.operations:
            if isinstance(operation, dict):
                operation = Runcard.GatesSettings.OperationSettings(**operation)
            assert isinstance(
                gates_settings.get_operation_settings(name=operation.name),
                gates_settings.OperationSettings,
            )

    def test_get_operation_settings_raises_error_when_operation_does_not_exist(self, gates_settings):
        """Test the ``get_gate`` method of the GateSettings class."""
        name = "unkown_operation"
        with pytest.raises(ValueError, match=f"Operation {name} not found in gate settings."):
            gates_settings.get_operation_settings(name)

    def test_get_gate(self, gates_settings):
        """Test the ``get_gate`` method of the GateSettings class."""
        gates_qubits = [
            (re.search(GATE_ALIAS_REGEX, alias)["gate"], re.search(GATE_ALIAS_REGEX, alias)["qubits"])
            for alias in gates_settings.gates.keys()
        ]
        assert all(
            isinstance(gate_event, GateEventSettings)
            for gate_name, gate_qubits in gates_qubits
            for gate_event in gates_settings.get_gate(name=gate_name, qubits=ast.literal_eval(gate_qubits))
        )

    def test_get_gate_raises_error(self, gates_settings):
        """Test that the ``get_gate`` method raises an error when the name is not found."""
        name = "test"
        qubits = 0

        error_string = re.escape(f"Gate {name} for qubits {qubits} not found in settings").replace(
            "\\", ""
        )  # fixes re.escape bug
        with pytest.raises(KeyError, match=error_string):
            gates_settings.get_gate(name, qubits=qubits)

    def test_gate_names(self, gates_settings):
        """Test the ``gate_names`` method of the GateSettings class."""
        expected_names = list(gates_settings.gates.keys())
        assert gates_settings.gate_names == expected_names

    def test_set_platform_parameters(self, gates_settings):
        """Test that with ``set_parameter`` we can change all settings of the platform."""
        gates_settings.set_parameter(parameter=Parameter.DELAY_BEFORE_READOUT, value=1234)
        assert gates_settings.delay_before_readout == 1234

        gates_settings.set_parameter(parameter=Parameter.DELAY_BETWEEN_PULSES, value=1234)
        assert gates_settings.delay_between_pulses == 1234

    @pytest.mark.parametrize("alias", ["X(0)", "M(0)"])
    def test_set_gate_parameters(self, alias: str, gates_settings):
        """Test that with ``set_parameter`` we can change all settings of the platform's gates."""
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        assert regex_match is not None

        name = regex_match["gate"]
        qubits_str = regex_match["qubits"]
        qubits = ast.literal_eval(qubits_str)

        gates_settings.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
        assert gates_settings.get_gate(name=name, qubits=qubits)[0].pulse.duration == 1234

        gates_settings.set_parameter(alias=alias, parameter=Parameter.PHASE, value=1234)
        assert gates_settings.get_gate(name=name, qubits=qubits)[0].pulse.phase == 1234

        gates_settings.set_parameter(alias=alias, parameter=Parameter.AMPLITUDE, value=1234)
        assert gates_settings.get_gate(name=name, qubits=qubits)[0].pulse.amplitude == 1234

    @pytest.mark.parametrize("alias", ["X(0,)", "X()", "X", ""])
    def test_set_gate_parameters_raises_error_when_alias_has_incorrect_format(self, alias: str, gates_settings):
        """Test that with ``set_parameter`` will raise error when alias has incorrect format"""
        with pytest.raises(ValueError, match=re.escape(f"Alias {alias} has incorrect format")):
            gates_settings.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
