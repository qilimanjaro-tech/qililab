"""Unit tests for the Runcard class."""

import ast
import copy
import re
from dataclasses import asdict
from warnings import catch_warnings, simplefilter

import pytest

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings import Runcard, DigitalCompilationSettings, AnalogCompilationSettings
from qililab.settings.analog.flux_control_topology import FluxControlTopology
from qililab.settings.digital.gate_event import GateEvent
from qililab.typings import Parameter
from tests.data import Galadriel


@pytest.fixture(name="runcard")
def fixture_runcard():
    return Runcard(**copy.deepcopy(Galadriel.runcard))


@pytest.fixture(name="digital")
def fixture_digital_compilation_settings(runcard: Runcard):
    return runcard.digital

@pytest.fixture(name="analog")
def fixture_analog_compilation_settings(runcard: Runcard):
    return runcard.analog


class TestRuncard:
    """Unit tests for the Runcard dataclass initialization."""

    def test_attributes(self, runcard: Runcard):
        """Test that the attributes of the Runcard are casted into dataclasses, and that
        the values they contain are the same as the input dictionaries."""

        assert isinstance(runcard.name, str)
        assert isinstance(runcard.instruments, list)
        assert isinstance(runcard.instruments[0], dict)
        assert isinstance(runcard.buses, list)
        assert isinstance(runcard.digital, DigitalCompilationSettings)
        assert isinstance(runcard.analog, AnalogCompilationSettings)


class TestDigitalCompilationSettings:
    """Unit tests for the DigitalCompilationSettings class."""

    def test_attributes(self, digital: DigitalCompilationSettings):
        """Test that the Runcard.GatesSettings dataclass contains the right attributes."""
        assert isinstance(digital.gates, dict)
        assert all(
            (isinstance(key, str), isinstance(event, GateEvent))
            for key, settings in digital.gates.items()
            for event in settings
        )

    def test_get_parameter_fails(self, digital: DigitalCompilationSettings):
        with pytest.raises(ValueError, match="Could not find gate alias in gate settings."):
            digital.get_parameter(alias="alias", parameter=Parameter.DURATION)

        with pytest.raises(ValueError):
            digital.get_parameter(alias="non-existent-bus", parameter=Parameter.DELAY)

    def test_get_gate(self, digital):
        """Test the ``get_gate`` method of the Runcard.GatesSettings class."""
        gates_qubits = [
            (re.search(GATE_ALIAS_REGEX, alias)["gate"], re.search(GATE_ALIAS_REGEX, alias)["qubits"])
            for alias in digital.gates.keys()
        ]
        assert all(
            isinstance(gate_event, GateEvent)
            for gate_name, gate_qubits in gates_qubits
            for gate_event in digital.get_gate(name=gate_name, qubits=ast.literal_eval(gate_qubits))
        )

        # check that CZs commute
        # CZ(0,1) doesn't have spaces in the tuple string
        assert isinstance(digital.get_gate(name="CZ", qubits=(1, 0))[0], GateEvent)
        assert isinstance(digital.get_gate(name="CZ", qubits=(0, 1))[0], GateEvent)

        # CZ(0, 2) has spaces in the tuple string
        assert isinstance(digital.get_gate(name="CZ", qubits=(2, 0))[0], GateEvent)
        assert isinstance(digital.get_gate(name="CZ", qubits=(0, 2))[0], GateEvent)

    def test_get_gate_raises_error(self, digital):
        """Test that the ``get_gate`` method raises an error when the name is not found."""
        name = "test"
        qubits = 0

        error_string = re.escape(f"Gate {name} for qubits {qubits} not found in settings").replace(
            "\\", ""
        )  # fixes re.escape bug
        with pytest.raises(KeyError, match=error_string):
            digital.get_gate(name, qubits=qubits)

    def test_gate_names(self, digital: DigitalCompilationSettings):
        """Test the ``gate_names`` method of the Runcard.GatesSettings class."""
        expected_names = list(digital.gates.keys())
        assert digital.gate_names == expected_names

    def test_set_parameter_fails(self, digital: DigitalCompilationSettings):
        with pytest.raises(ValueError):
            digital.set_parameter(alias="non-existent-bus", parameter=Parameter.DELAY, value=123)

    @pytest.mark.parametrize("alias", ["X(0)", "M(0)"])
    def test_set_gate_parameters(self, alias: str, digital: DigitalCompilationSettings):
        """Test that with ``set_parameter`` we can change all settings of the platform's gates."""
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        assert regex_match is not None

        name = regex_match["gate"]
        qubits_str = regex_match["qubits"]
        qubits = ast.literal_eval(qubits_str)

        digital.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
        assert digital.get_gate(name=name, qubits=qubits)[0].pulse.duration == 1234

        digital.set_parameter(alias=alias, parameter=Parameter.PHASE, value=1234)
        assert digital.get_gate(name=name, qubits=qubits)[0].pulse.phase == 1234

        digital.set_parameter(alias=alias, parameter=Parameter.AMPLITUDE, value=1234)
        assert digital.get_gate(name=name, qubits=qubits)[0].pulse.amplitude == 1234

    @pytest.mark.parametrize("alias", ["X(0,)", "X()", "X", ""])
    def test_set_gate_parameters_raises_error_when_alias_has_incorrect_format(self, alias: str, digital):
        """Test that with ``set_parameter`` will raise error when alias has incorrect format"""
        with pytest.raises(ValueError, match=re.escape(f"Alias {alias} has incorrect format")):
            digital.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)

class TestAnalogCompilationSettings:
    """Unit tests for the DigitalCompilationSettings class."""

    def test_attributes(self, analog: AnalogCompilationSettings):
        assert isinstance(analog.flux_control_topology, list)
        assert all(isinstance(topology, FluxControlTopology) for topology in analog.flux_control_topology)
