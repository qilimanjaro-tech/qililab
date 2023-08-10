"""Unit tests for the Runcard class."""
import ast
import re
from dataclasses import asdict

import pytest

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings import Runcard
from qililab.typings import Parameter
from tests.data import Galadriel


@pytest.mark.parametrize("runcard_dict", [Galadriel.runcard])
class TestRuncard:
    """Unit tests for the Runcard dataclass initialization."""

    def test_attributes(self, runcard_dict):
        """Test that the attributes of the Runcard are casted into dataclasses, and that
        the values they contain are the same as the input dictionaries."""
        runcard = Runcard(**runcard_dict)

        assert isinstance(runcard.transpilation_settings, runcard.TranspilationSettings)
        assert asdict(runcard.transpilation_settings) == Galadriel.platform

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


@pytest.mark.parametrize("transpilation_settings", [Runcard(**Galadriel.runcard).transpilation_settings])
class TestTranspilationSettings:
    """Unit tests for the Runcard.TranspilationSettings class."""

    def test_attributes(self, transpilation_settings):
        """Test that the Runcard.TranspilationSettings dataclass contains the right attributes."""
        assert isinstance(transpilation_settings.name, str)
        assert isinstance(transpilation_settings.delay_between_pulses, int)
        assert isinstance(transpilation_settings.delay_before_readout, int)
        assert isinstance(transpilation_settings.gates, dict)
        assert isinstance(transpilation_settings.gates[0], list)
        assert isinstance(transpilation_settings.gates[0][0], transpilation_settings.GateSettings)
        assert isinstance(transpilation_settings.reset_method, str)
        assert isinstance(transpilation_settings.passive_reset_duration, int)
        assert isinstance(transpilation_settings.operations, list)

    def test_get_operation_settings(self, transpilation_settings):
        """Test the ``get_operation_settings`` method of the PlatformSettings class."""
        for operation in transpilation_settings.operations:
            if isinstance(operation, dict):
                operation = Runcard.TranspilationSettings.OperationSettings(**operation)
            assert isinstance(
                transpilation_settings.get_operation_settings(name=operation.name),
                transpilation_settings.OperationSettings,
            )

    def test_get_operation_settings_raises_error_when_operation_does_not_exist(self, transpilation_settings):
        """Test the ``get_gate`` method of the PlatformSettings class."""
        name = "unkown_operation"
        with pytest.raises(ValueError, match=f"Operation {name} not found in platform settings."):
            transpilation_settings.get_operation_settings(name)

    def test_get_gate(self, transpilation_settings):
        """Test the ``get_gate`` method of the PlatformSettings class."""
        for qubit, gate_list in transpilation_settings.gates.items():
            for gate in gate_list:
                assert transpilation_settings.get_gate(name=gate.name, qubits=qubit) is gate

    def test_get_gate_raises_error(self, transpilation_settings):
        """Test that the ``get_gate`` method raises an error when the name is not found."""
        name = "test"
        qubits = 0

        with pytest.raises(ValueError, match=f"Gate {name} for qubits {qubits} not found in settings"):
            transpilation_settings.get_gate(name, qubits=qubits)

    def test_gate_names(self, transpilation_settings):
        """Test the ``gate_names`` method of the PlatformSettings class."""
        expected_names = list({gate.name for gates in transpilation_settings.gates.values() for gate in gates})

        assert transpilation_settings.gate_names == expected_names

    def test_set_platform_parameters(self, transpilation_settings):
        """Test that with ``set_parameter`` we can change all settings of the platform."""
        transpilation_settings.set_parameter(parameter=Parameter.DELAY_BEFORE_READOUT, value=1234)
        assert transpilation_settings.delay_before_readout == 1234

        transpilation_settings.set_parameter(parameter=Parameter.DELAY_BETWEEN_PULSES, value=1234)
        assert transpilation_settings.delay_between_pulses == 1234

    @pytest.mark.parametrize("alias", ["X(0)", "X(1)", "M(0)", "M(1)", "M(0,1)", "M(1,0)"])
    def test_set_gate_parameters(self, alias: str, transpilation_settings):
        """Test that with ``set_parameter`` we can change all settings of the platform's gates."""
        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        assert regex_match is not None

        name = regex_match["gate"]
        qubits_str = regex_match["qubits"]
        qubits = ast.literal_eval(qubits_str)

        transpilation_settings.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
        assert transpilation_settings.get_gate(name=name, qubits=qubits).duration == 1234

        transpilation_settings.set_parameter(alias=alias, parameter=Parameter.PHASE, value=1234)
        assert transpilation_settings.get_gate(name=name, qubits=qubits).phase == 1234

        transpilation_settings.set_parameter(alias=alias, parameter=Parameter.AMPLITUDE, value=1234)
        assert transpilation_settings.get_gate(name=name, qubits=qubits).amplitude == 1234

    @pytest.mark.parametrize("alias", ["X(0,)", "X()", "X", ""])
    def test_set_gate_parameters_raises_error_when_alias_has_incorrect_format(self, alias: str, transpilation_settings):
        """Test that with ``set_parameter`` will raise error when alias has incorrect format"""
        with pytest.raises(ValueError, match=re.escape(f"Alias {alias} has incorrect format")):
            transpilation_settings.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
