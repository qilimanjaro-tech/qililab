"""Unit tests for the RuncardSchema class."""
from dataclasses import asdict

import pytest

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
            if isinstance(operation, dict):
                operation = RuncardSchema.PlatformSettings.OperationSettings(**operation)
            assert isinstance(settings.get_operation_settings(name=operation.name), settings.OperationSettings)

    def test_get_operation_settings_raises_error_when_operation_does_not_exist(self):
        """Test the ``get_gate`` method of the PlatformSettings class."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        name = "unkown_operation"
        with pytest.raises(ValueError, match=f"Operation {name} not found in platform settings."):
            settings.get_operation_settings(name)

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

    def test_set_gate_parameters(self):
        """Test that with ``set_parameter`` we can change all settings of the platform's gates."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        settings.set_parameter(alias="M.0", parameter=Parameter.DURATION, value=1234)
        assert settings.get_gate("M", qubits=0).duration == 1234

        settings.set_parameter(alias="Y.0", parameter=Parameter.PHASE, value=1234)
        assert settings.get_gate("Y", qubits=0).phase == 1234

        settings.set_parameter(alias="I.0", parameter=Parameter.AMPLITUDE, value=1234)
        assert settings.get_gate("I", qubits=0).amplitude == 1234

        settings.set_parameter(alias="X.0", parameter=Parameter.DRAG_COEFFICIENT, value=1234)
        assert settings.get_gate("X", qubits=0).shape["drag_coefficient"] == 1234
