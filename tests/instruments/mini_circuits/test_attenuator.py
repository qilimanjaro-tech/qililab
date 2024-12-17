import pytest
from unittest.mock import MagicMock
from qililab.instruments.mini_circuits.attenuator import Attenuator
from qililab.instruments.instrument import ParameterNotFound
from qililab.typings import Parameter
from qililab.typings.instruments.mini_circuits import MiniCircuitsDriver

@pytest.fixture
def attenuator_settings():
    return {
        "alias": "attenuator_1",
        "attenuation": 10.0
    }

@pytest.fixture
def attenuator(attenuator_settings):
    attenuator = Attenuator(settings=attenuator_settings)
    attenuator.device = MagicMock(spec=MiniCircuitsDriver)
    return attenuator

class TestAttenuator:

    def test_attenuator_initialization(self, attenuator, attenuator_settings):
        assert attenuator.alias == "attenuator_1"
        assert attenuator.settings.alias == "attenuator_1"
        assert attenuator.settings.attenuation == 10.0
        assert attenuator.device is not None

    def test_attenuator_str(self, attenuator):
        assert str(attenuator) == "attenuator_1"

    def test_attenuator_attenuation_property(self, attenuator):
        assert attenuator.attenuation == 10.0

    def test_set_parameter_attenuation(self, attenuator):
        # Test setting attenuation parameter
        attenuator.set_parameter(Parameter.ATTENUATION, 15.0)
        assert attenuator.attenuation == 15.0
        attenuator.device.setup.assert_called_once_with(attenuation=15.0)

    def test_set_parameter_invalid(self, attenuator):
        # Test setting an invalid parameter
        with pytest.raises(ParameterNotFound):
            attenuator.set_parameter(Parameter.BUS_FREQUENCY, 42.0)

    def test_get_parameter_attenuation(self, attenuator):
        # Test setting attenuation parameter
        attenuator.get_parameter(Parameter.ATTENUATION)
        assert attenuator.attenuation == 10.0

    def test_get_parameter_invalid(self, attenuator):
        # Test setting an invalid parameter
        with pytest.raises(ParameterNotFound):
            attenuator.get_parameter(Parameter.BUS_FREQUENCY)

    def test_initial_setup(self, attenuator):
        # Test initial setup of the attenuator
        attenuator.initial_setup()
        attenuator.device.setup.assert_called_once_with(attenuation=attenuator.attenuation)

    def test_turn_on(self, attenuator):
        # No specific implementation in the provided code, just test invocation
        assert attenuator.turn_on() is None

    def test_turn_off(self, attenuator):
        # No specific implementation in the provided code, just test invocation
        assert attenuator.turn_off() is None

    def test_reset(self, attenuator):
        # No specific implementation in the provided code, just test invocation
        assert attenuator.reset() is None
