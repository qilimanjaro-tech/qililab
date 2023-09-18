"""Unit tests for the Runcard class."""
import ast
import copy
import re
from dataclasses import asdict

import pytest

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings import NewRuncard
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.typings import Parameter
from tests.data import NewGaladriel


@pytest.fixture(name="runcard")
def fixture_runcard():
    return NewRuncard(**copy.deepcopy(NewGaladriel.runcard))


@pytest.fixture(name="gates_settings")
def fixture_gate_settings(runcard: NewRuncard):
    return runcard.gates_settings


class TestNewRuncard:
    """Unit tests for the Runcard dataclass initialization."""

    def test_attributes(self, runcard: NewRuncard):
        """Test that the attributes of the Runcard are casted into dataclasses, and that
        the values they contain are the same as the input dictionaries."""

        assert isinstance(runcard.name, str)
        assert runcard.name == NewGaladriel.runcard["name"]

        assert isinstance(runcard.device_id, int)
        assert runcard.device_id == NewGaladriel.runcard["device_id"]

        assert isinstance(runcard.gates_settings, runcard.GatesSettings)
        assert asdict(runcard.gates_settings) == NewGaladriel.runcard["gates_settings"]

        assert isinstance(runcard.chip, runcard.Chip)
        assert asdict(runcard.chip) == NewGaladriel.runcard["chip"]

        assert isinstance(runcard.instruments, list)
        assert isinstance(runcard.instruments[0], dict)
        for index, instrument in enumerate(runcard.instruments):
            assert instrument == NewGaladriel.runcard["instruments"][index]

    def test_serialization(self, runcard):
        """Test that a serialization of the Platform is possible"""

        runcard_dict = asdict(runcard)
        assert isinstance(runcard_dict, dict)

        new_runcard = NewRuncard(**runcard_dict)
        assert isinstance(new_runcard, NewRuncard)
        assert str(new_runcard) == str(runcard)
        assert str(new_runcard.name) == str(runcard.name)
        assert str(new_runcard.device_id) == str(runcard.device_id)
        assert str(new_runcard.chip) == str(runcard.chip)
        assert str(new_runcard.instruments) == str(runcard.instruments)

        new_runcard_dict = asdict(new_runcard)
        assert isinstance(new_runcard_dict, dict)
        assert new_runcard_dict == runcard_dict


class TestGatesSettings:
    """Unit tests for the Runcard.GatesSettings class."""

    def test_attributes(self, gates_settings):
        """Test that the Runcard.GatesSettings dataclass contains the right attributes."""
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
        """Test the ``get_operation_settings`` method of the Runcard.GatesSettings class."""
        for operation in gates_settings.operations:
            if isinstance(operation, dict):
                operation = NewRuncard.GatesSettings.OperationSettings(**operation)
            assert isinstance(
                gates_settings.get_operation_settings(name=operation.name),
                gates_settings.OperationSettings,
            )

    def test_get_operation_settings_raises_error_when_operation_does_not_exist(self, gates_settings):
        """Test the ``get_gate`` method of the Runcard.GatesSettings class."""
        name = "unkown_operation"
        with pytest.raises(ValueError, match=f"Operation {name} not found in gates settings."):
            gates_settings.get_operation_settings(name)

    def test_get_gate(self, gates_settings):
        """Test the ``get_gate`` method of the Runcard.GatesSettings class."""
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
        """Test the ``gate_names`` method of the Runcard.GatesSettings class."""
        expected_names = list(gates_settings.gates.keys())
        assert gates_settings.gate_names == expected_names

    def test_set_platform_parameters(self, gates_settings):
        """Test that with ``set_parameter`` we can change all settings of the platform."""
        gates_settings.set_parameter(parameter=Parameter.DELAY_BEFORE_READOUT, value=1234)
        assert gates_settings.delay_before_readout == 1234

        gates_settings.set_parameter(parameter=Parameter.DELAY_BETWEEN_PULSES, value=1234)
        assert gates_settings.delay_between_pulses == 1234
