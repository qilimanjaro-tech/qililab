"""Unit tests for the RuncardSchema class."""
import ast
import re
from dataclasses import asdict

import pytest

from qililab.constants import GATE_ALIAS_REGEX
from qililab.settings import RuncardSchema
from qililab.typings import Parameter
from tests.data import Galadriel


class TestRuncardSchema:
    """Unit tests for the RuncardSchema class."""

    def test_attributes(self):
        """Test that the attributes of the RuncardSchema are casted into dataclasses, and that
        the values they contain are the same as the input dictionaries."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        assert isinstance(runcard.settings, runcard.PlatformSettings)
        assert asdict(runcard.settings) == Galadriel.platform
        assert isinstance(runcard.schema, runcard.Schema)
        assert asdict(runcard.schema) == Galadriel.schema


class TestSchema:
    """Unit tests for the RuncardSchema.Schema class."""

    def test_attributes(self):
        """Test that the RuncardSchema.Schema dataclass contains the right attributes."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        schema = runcard.schema

        assert isinstance(schema.chip, schema.ChipSchema)
        assert asdict(schema.chip) == Galadriel.chip
        assert isinstance(schema.buses, list)
        assert isinstance(schema.buses[0], schema.BusSchema)
        assert [asdict(bus) for bus in schema.buses] == Galadriel.buses
        assert isinstance(schema.instruments, list)
        assert isinstance(schema.instruments[0], dict)
        assert schema.instruments == Galadriel.instruments
        assert isinstance(schema.instrument_controllers, list)
        assert isinstance(schema.instrument_controllers[0], dict)
        assert schema.instrument_controllers == Galadriel.instrument_controllers


class TestPlatformSettings:
    """Unit tests for the RuncardSchema.PlatformSettings class."""

    def test_attributes(self):
        """Test that the RuncardSchema.PlatformSettings dataclass contains the right attributes."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        assert isinstance(settings.name, str)
        assert isinstance(settings.delay_between_pulses, int)
        assert isinstance(settings.delay_before_readout, int)
        assert isinstance(settings.master_amplitude_gate, (int, float))
        assert isinstance(settings.master_duration_gate, int)
        assert isinstance(settings.gates, dict)
        assert isinstance(settings.gates[0], list)
        assert isinstance(settings.gates[0][0], settings.GateSettings)
        assert isinstance(settings.reset_method, str)
        assert isinstance(settings.passive_reset_duration, int)
        assert isinstance(settings.operations, list)

    def test_get_operation_settings(self):
        """Test the ``get_operation_settings`` method of the PlatformSettings class."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        for operation in settings.operations:
            assert isinstance(settings.get_operation_settings(name=operation.name), settings.OperationSettings)

    def test_get_gate(self):
        """Test the ``get_gate`` method of the PlatformSettings class."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        for qubit, gate_list in settings.gates.items():
            for gate in gate_list:
                assert settings.get_gate(name=gate.name, qubits=qubit) is gate

    def test_get_gate_raises_error(self):
        """Test that the ``get_gate`` method raises an error when the name is not found."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        name = "test"
        qubits = 0

        with pytest.raises(ValueError, match=f"Gate {name} for qubits {qubits} not found in settings"):
            settings.get_gate(name, qubits=qubits)

    def test_gate_names(self):
        """Test the ``gate_names`` method of the PlatformSettings class."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        expected_names = list({gate.name for gates in settings.gates.values() for gate in gates})

        assert settings.gate_names == expected_names

    def test_operation_names_property(self):
        """Test the ``operation_names`` method of the PlatformSettings class."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        expected_names = [operation.name for operation in settings.operations]

        assert settings.operation_names == expected_names

    def test_set_platform_parameters(self):
        """Test that with ``set_parameter`` we can change all settings of the platform."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        settings.set_parameter(parameter=Parameter.DELAY_BEFORE_READOUT, value=1234)
        assert settings.delay_before_readout == 1234

        settings.set_parameter(parameter=Parameter.DELAY_BETWEEN_PULSES, value=1234)
        assert settings.delay_between_pulses == 1234

        settings.set_parameter(parameter=Parameter.MASTER_AMPLITUDE_GATE, value=1234)
        assert settings.master_amplitude_gate == 1234

        settings.set_parameter(parameter=Parameter.MASTER_DURATION_GATE, value=1234)
        assert settings.master_duration_gate == 1234

    @pytest.mark.parametrize("alias", ["X(0)", "X(1)", "M(0)", "M(1)", "M(0,1)", "M(1,0)"])
    def test_set_gate_parameters(self, alias: str):
        """Test that with ``set_parameter`` we can change all settings of the platform's gates."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)  # type: ignore
        settings = runcard.settings

        regex_match = re.search(GATE_ALIAS_REGEX, alias)
        assert regex_match is not None

        name = regex_match.group("gate")
        qubits_str = regex_match.group("qubits")
        qubits = ast.literal_eval(qubits_str)

        settings.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
        assert settings.get_gate(name=name, qubits=qubits).duration == 1234

        settings.set_parameter(alias=alias, parameter=Parameter.PHASE, value=1234)
        assert settings.get_gate(name=name, qubits=qubits).phase == 1234

        settings.set_parameter(alias=alias, parameter=Parameter.AMPLITUDE, value=1234)
        assert settings.get_gate(name=name, qubits=qubits).amplitude == 1234

    @pytest.mark.parametrize("alias", ["X(0,)", "X()", "X", ""])
    def test_set_gate_parameters_raises_error_when_alias_has_incorrect_format(self, alias: str):
        """Test that with ``set_parameter`` will raise error when alias has incorrect format"""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)  # type: ignore
        settings = runcard.settings

        with pytest.raises(ValueError, match=re.escape(f"Alias {alias} has incorrect format")):
            settings.set_parameter(alias=alias, parameter=Parameter.DURATION, value=1234)
