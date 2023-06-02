"""Tests for the SystemControl class."""
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.platform import Platform
from qililab.platform.components import BusElement
from qililab.system_control import SystemControl
from qililab.typings import FactoryElement
from qililab.typings.enums import Parameter
from tests.data import Galadriel
from tests.utils import platform_db


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=Galadriel.runcard)


@pytest.fixture(name="system_control")
def fixture_system_control(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {
        "id_": 1,
        "category": "system_control",
        "instruments": ["QCM", "rs_1"],
    }
    return SystemControl(settings=settings, platform_instruments=platform.instruments)


class TestInstument:
    """Unit tests checking the ``SystemControl`` methods."""

    def test_error_raises_instrument_not_connected(self, system_control: SystemControl):
        """ "Test Parameter error raises if the parameter is not found."""
        name = system_control.instruments[0].name.value
        with pytest.raises(
            ValueError,
            match=f"Instrument {name} is not connected and cannot set the new value: 45 to the parameter voltage.",
        ):
            system_control.set_parameter(parameter="voltage", value="45", channel_id=1)  # type: ignore

    def test_get_hw_values_raises(self, system_control: SystemControl):
        """Test abstract method get_hw_values method raises if called directly without instantiating any type of instrument"""
        parameter = Parameter.AMPLITUDE
        instrument = system_control.instruments[0]
        name = instrument.name.value
        with pytest.raises(
            ValueError,
            match=f"Instrument {name} is not connected and cannot retrieve values from the parameter {parameter}.",
        ):
            instrument.get_hw_values(parameter=parameter)  # type: ignore

    def test_retrieve_hw_values_raises(self, system_control: SystemControl):
        """Test abstract method retrieve_hw_values method raises if called directly without instantiating any type of instrument"""
        parameter = Parameter.AMPLITUDE
        instrument = system_control.instruments[0]
        instrument.device = MagicMock()
        name = instrument.name.value
        with pytest.raises(
            ParameterNotFound, match=f"Instrument {name} is does not support hardware loops for parameter {parameter}."
        ):
            instrument.retrieve_hw_values(parameter=parameter)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_setup_raises(self, system_control: SystemControl):
        """Test abstract method of Instrument raises if called directly without instantiating any type of instrument"""
        parameter = Parameter.AMPLITUDE
        instrument = system_control.instruments[0]
        instrument.device = MagicMock()
        name = instrument.name1
        with pytest.raises(ParameterNotFound, match=f"Could not find parameter {parameter} in instrument {name}"):
            instrument.setup(parameter=parameter, value=0.0, channel_id=1)  # type: ignore

    def test_device_initialized_raises(self, system_control: SystemControl):
        """Test CheckDeviceInitialized raises exception when device is not initialized"""
        instrument = system_control.instruments[0]
        with pytest.raises(AttributeError, match="Instrument Device has not been initialized"):
            instrument.setup(parameter=Parameter.AMPLITUDE)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_value_not_given_int_float(self, system_control: SystemControl):
        """Test that CheckParameterValueFloatOrInt raises when no value is given"""
        instrument = system_control.instruments[0]
        with pytest.raises(ValueError, match="'value' not specified to update instrument settings."):
            instrument.set_parameter(parameter=Parameter.AMPLITUDE)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_value_not_int_ot_float(self, system_control: SystemControl):
        """Test that CheckParameterValueFloatOrInt raises when value is not an int nor float"""
        value = "foobar"
        with pytest.raises(ValueError, match=f"value must be a float or an int. Current type: {type(value)}"):
            system_control.set_parameter(parameter=Parameter.AMPLITUDE, value=value)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_value_not_given_bool(self, system_control: SystemControl):
        """Test that CheckParameterValueFloatOrInt raises when no value is given"""
        with pytest.raises(ValueError, match="'value' not specified to update instrument settings."):
            system_control.set_parameter(parameter=Parameter.AMPLITUDE)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_value_not_bool(self, system_control: SystemControl):
        """Test that CheckParameterValueFloatOrInt raises when value is not an int nor float"""
        value = "foobar"
        with pytest.raises(ValueError, match=f"value must be a bool. Current type: {type(value)}"):
            system_control.set_parameter(parameter=Parameter.AMPLITUDE, value=value)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_value_not_given_string(self, system_control: SystemControl):
        """Test that CheckParameterValueFloatOrInt raises when no value is given"""
        with pytest.raises(ValueError, match="'value' not specified to update instrument settings."):
            system_control.set_parameter(parameter=Parameter.AMPLITUDE)

    @pytest.mark.skip(reason="no way of currently testing this")
    def test_value_not_string(self, system_control: SystemControl):
        """Test that CheckParameterValueFloatOrInt raises when value is not an int nor float"""
        value = 0.0
        with pytest.raises(ValueError, match=f"value must be a string. Current type: {type(value)}"):
            system_control.set_parameter(parameter=Parameter.AMPLITUDE, value=value)
