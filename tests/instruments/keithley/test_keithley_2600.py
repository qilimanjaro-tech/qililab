"""Tests for the Keithley2600 class."""
import pytest
from unittest import mock
from qililab.instruments import ParameterNotFound
from qililab.typings import Parameter, InstrumentName
from qililab.instruments.utils import InstrumentFactory
import numpy as np

@pytest.fixture
def keithley2600():
    # Instantiate the Keithley2600 with mocked device and settings
    settings = {
        "alias": "keithley",
        "max_current": 1.0,
        "max_voltage": 10.0
    }
    Keithley2600 = InstrumentFactory.get(InstrumentName.KEITHLEY2600)
    instrument = Keithley2600(settings=settings)
    instrument.device = mock.Mock()
    instrument.device.smua = mock.Mock()
    return instrument


class TestKeithley2600:

    def test_set_parameter_max_current(self, keithley2600):
        # Test setting max current
        keithley2600.set_parameter(Parameter.MAX_CURRENT, 2.0)

        assert keithley2600.max_current == 2.0
        keithley2600.device.smua.limiti.assert_called_with(2.0)

    def test_set_parameter_max_voltage(self, keithley2600):
        # Test setting max voltage
        keithley2600.set_parameter(Parameter.MAX_VOLTAGE, 20.0)

        assert keithley2600.max_voltage == 20.0
        keithley2600.device.smua.limitv.assert_called_with(20.0)

    def test_set_parameter_invalid(self, keithley2600):
        # Test setting an invalid parameter
        with pytest.raises(ParameterNotFound):
            keithley2600.set_parameter("INVALID_PARAMETER", 100)

    def test_initial_setup(self, keithley2600):
        # Test initial setup to ensure it calls the device methods correctly
        keithley2600.initial_setup()

        keithley2600.device.smua.limiti.assert_called_with(keithley2600.max_current)
        keithley2600.device.smua.limitv.assert_called_with(keithley2600.max_voltage)

    def test_turn_on(self, keithley2600):
        # Placeholder test for the turn_on method, which could involve more device actions
        keithley2600.turn_on()
        # Add assertions if turn_on has real behavior in the future

    def test_turn_off(self, keithley2600):
        # Placeholder test for the turn_off method, which could involve more device actions
        keithley2600.turn_off()
        # Add assertions if turn_off has real behavior in the future

    def test_reset(self, keithley2600):
        # Test reset method to ensure it calls device.reset
        keithley2600.reset()
        keithley2600.device.reset.assert_called_once()

    def test_fast_sweep(self, keithley2600):
        # Mock the fast sweep return data
        mock_sweep_data = mock.Mock()
        mock_sweep_data.to_xarray.return_value.to_array.return_value.values.squeeze.return_value = np.array([0.1, 0.2, 0.3])
        keithley2600.device.smua.doFastSweep.return_value = mock_sweep_data

        start, stop, steps = 0.0, 10.0, 3
        x_values, data = keithley2600.fast_sweep(start, stop, steps, mode='IV')

        expected_x_values = np.linspace(start, stop, steps)
        np.testing.assert_array_equal(x_values, expected_x_values)
        np.testing.assert_array_equal(data, np.array([0.1, 0.2, 0.3]))

    def test_max_current_getter(self, keithley2600):
        # Test the max_current getter
        assert keithley2600.max_current == keithley2600.settings.max_current

    def test_max_current_setter(self, keithley2600):
        # Test the max_current setter
        keithley2600.max_current = 5.0
        assert keithley2600.settings.max_current == 5.0
        keithley2600.device.smua.limiti.assert_called_with(5.0)

    def test_max_voltage_getter(self, keithley2600):
        # Test the max_voltage getter
        assert keithley2600.max_voltage == keithley2600.settings.max_voltage

    def test_max_voltage_setter(self, keithley2600):
        # Test the max_voltage setter
        keithley2600.max_voltage = 50.0
        assert keithley2600.settings.max_voltage == 50.0
        keithley2600.device.smua.limitv.assert_called_with(50.0)
