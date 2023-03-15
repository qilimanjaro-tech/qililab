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
        assert isinstance(settings.gates, list)
        assert isinstance(settings.gates[0], settings.GateSettings)

    def test_get_gate(self):
        """Test the ``get_gate`` method of the PlatformSettings class."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        for gate in settings.gates:
            assert settings.get_gate(name=gate.name) is gate

    def test_get_gate_raises_error(self):
        """Test that the ``get_gate`` method raises an error when the name is not found."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        name = "test"

        with pytest.raises(ValueError, match=f"Gate {name} not found in settings"):
            settings.get_gate(name)

    def test_gate_names(self):
        """Test the ``gate_names`` method of the PlatformSettings class."""
        runcard = RuncardSchema(settings=Galadriel.platform, schema=Galadriel.schema)
        settings = runcard.settings

        expected_names = [g.name for g in settings.gates]

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

        settings.set_parameter(alias="M", parameter=Parameter.DURATION, value=1234)
        assert settings.get_gate("M").duration == 1234

        settings.set_parameter(alias="Y", parameter=Parameter.PHASE, value=1234)
        assert settings.get_gate("Y").phase == 1234

        settings.set_parameter(alias="I", parameter=Parameter.AMPLITUDE, value=1234)
        assert settings.get_gate("I").amplitude == 1234

        settings.set_parameter(alias="X", parameter=Parameter.DRAG_COEFFICIENT, value=1234)
        assert settings.get_gate("X").shape["drag_coefficient"] == 1234
