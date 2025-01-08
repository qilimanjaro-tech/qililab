import pytest
from unittest.mock import MagicMock
from qililab.instruments import Instrument
from qililab.typings import Parameter, ParameterValue, ChannelID

# A concrete subclass of Instrument for testing purposes
class DummyInstrument(Instrument):
    def turn_on(self):
        return "Instrument turned on"

    def turn_off(self):
        return "Instrument turned off"

    def reset(self):
        return "Instrument reset"

    def initial_setup(self):
        return "Initial Setup"

    def get_parameter(self, parameter: Parameter, channel_id: ChannelID | None = None) -> ParameterValue:
        return "parameter_value"

    def set_parameter(self, parameter: Parameter, value: ParameterValue, channel_id: ChannelID | None = None):
        return True

@pytest.fixture
def instrument_settings():
    return {
        "alias": "test_instrument",
    }

@pytest.fixture
def instrument(instrument_settings):
    return DummyInstrument(settings=instrument_settings)

class TestInstrumentBase:
    """Test class for the Instrument abstract class, ensuring common functionality is tested."""

    def test_instrument_initialization(self, instrument, instrument_settings):
        assert instrument.alias == "test_instrument"
        assert instrument.settings.alias == "test_instrument"

    def test_instrument_str(self, instrument):
        assert str(instrument) == "test_instrument"

    def test_instrument_is_device_active(self, instrument):
        # Device is initially not set, so should return False
        assert instrument.is_device_active() is False

        # After setting a device, it should return True
        instrument.device = MagicMock()
        assert instrument.is_device_active() is True

    def test_instrument_turn_on(self, instrument):
        assert instrument.turn_on() == "Instrument turned on"

    def test_instrument_turn_off(self, instrument):
        assert instrument.turn_off() == "Instrument turned off"

    def test_instrument_reset(self, instrument):
        assert instrument.reset() == "Instrument reset"

    def test_instrument_get_parameter(self, instrument):
        parameter = MagicMock(spec=Parameter)
        assert instrument.get_parameter(parameter) == "parameter_value"

    def test_instrument_set_parameter(self, instrument):
        parameter = MagicMock(spec=Parameter)
        value = 42
        assert instrument.set_parameter(parameter, value) is True

    def test_instrument_is_awg(self, instrument):
        assert instrument.is_awg() is False  # Default implementation returns False

    def test_instrument_is_adc(self, instrument):
        assert instrument.is_adc() is False  # Default implementation returns False
