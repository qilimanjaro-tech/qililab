"""Tests for the Keithley2400 class."""
import re
import pytest
from unittest import mock
from qililab.instruments import ParameterNotFound
from qililab.typings import Parameter, InstrumentName
from qililab.instruments.utils import InstrumentFactory
import numpy as np

@pytest.fixture
def keithley2400_curr_mode():
    """Keithley2400 in current source mode."""
    settings = {
        "alias": "keithley",
        "mode": "CURR",
        "output": True,
        "current": 1e-3,
        "voltage": None,
    }
    Keithley2400 = InstrumentFactory.get(InstrumentName.KEITHLEY2400)
    instrument = Keithley2400(settings=settings)
    instrument.device = mock.Mock()
    instrument.is_device_active = mock.Mock(return_value=True)
    return instrument

@pytest.fixture
def keithley2400_volt_mode():
    """Keithley2400 in voltage source mode."""
    settings = {
        "alias": "keithley",
        "mode": "VOLT",
        "output": True,
        "current": None,
        "voltage": 1.0,
    }
    Keithley2400 = InstrumentFactory.get(InstrumentName.KEITHLEY2400)
    instrument = Keithley2400(settings=settings)
    instrument.device = mock.Mock()
    instrument.is_device_active = mock.Mock(return_value=True)
    return instrument
    
class TestKeithley2400:
    def test_set_current_parameter(self, keithley2400_curr_mode):
        # Test setting current
        keithley2400_curr_mode.set_parameter(Parameter.CURRENT, 2e-3)

        keithley2400_curr_mode.device.mode.assert_called_with("CURR")
        keithley2400_curr_mode.device.output.assert_called_with(True)
        keithley2400_curr_mode.device.curr.assert_called_with(2e-3)

    def test_set_voltage_parameter(self, keithley2400_volt_mode):
        # Test setting voltage
        keithley2400_volt_mode.set_parameter(Parameter.VOLTAGE, 2.5)

        keithley2400_volt_mode.device.mode.assert_called_with("VOLT")
        keithley2400_volt_mode.device.output.assert_called_with(True)
        keithley2400_volt_mode.device.volt.assert_called_with(2.5)

    def test_set_parameter_invalid(self, keithley2400_curr_mode):
        # Test setting an invalid parameter
        with pytest.raises(ParameterNotFound):
            keithley2400_curr_mode.set_parameter("INVALID_PARAMETER", 100)

    def test_get_voltage_in_current_mode(self, keithley2400_curr_mode):
        # Test getting current
        keithley2400_curr_mode.device.volt.return_value = 1.2
        value = keithley2400_curr_mode.get_parameter(Parameter.VOLTAGE)

        assert value == 1.2
        keithley2400_curr_mode.device.volt.assert_called_once()

    def test_get_current_in_voltage_mode(self, keithley2400_volt_mode):
        # Test setting voltage
        keithley2400_volt_mode.device.curr.return_value = 1e-6
        value = keithley2400_volt_mode.get_parameter(Parameter.CURRENT)

        assert value == 1e-6
        keithley2400_volt_mode.device.curr.assert_called_once()

    def test_initial_setup_current_mode(self, keithley2400_curr_mode):
        # Test initial setup to ensure it calls the device methods correctly in current mode
        keithley2400_curr_mode.initial_setup()

        keithley2400_curr_mode.device.mode.assert_called_with("CURR")
        keithley2400_curr_mode.device.output.assert_called_with(True)
        keithley2400_curr_mode.device.curr.assert_called_with(keithley2400_curr_mode.settings.current)

    def test_initial_setup_voltage_mode(self, keithley2400_volt_mode):
        # Test initial setup to ensure it calls the device methods correctly in voltage mode
        keithley2400_volt_mode.initial_setup()

        keithley2400_volt_mode.device.mode.assert_called_with("VOLT")
        keithley2400_volt_mode.device.output.assert_called_with(True)
        keithley2400_volt_mode.device.volt.assert_called_with(keithley2400_volt_mode.settings.voltage)

    def test_initial_setup_raises_error_missing_current(self):
        # Test initial setup to ensure it calls the device methods correctly in voltage mode
        settings = {
            "alias": "keithley",
            "mode": "CURR",
            "output": True,
            "current": None,
            "voltage": None,
        }
        Keithley2400 = InstrumentFactory.get(InstrumentName.KEITHLEY2400)
        instrument = Keithley2400(settings=settings)
        instrument.device = mock.Mock()

        error_string = "Mode set to CURRent but no current given."
        with pytest.raises(ValueError, match=error_string):
            instrument.initial_setup()

    def test_initial_setup_raises_error_missing_voltage(self):
        # Test initial setup to ensure it calls the device methods correctly in current mode
        settings = {
            "alias": "keithley",
            "mode": "VOLT",
            "output": True,
            "current": None,
            "voltage": None,
        }
        Keithley2400 = InstrumentFactory.get(InstrumentName.KEITHLEY2400)
        instrument = Keithley2400(settings=settings)
        instrument.device = mock.Mock()

        error_string = "Mode set to VOLTage but no voltage given."
        with pytest.raises(ValueError, match=error_string):
            instrument.initial_setup()

    def test_initial_setup_raises_error_missing_mode(self):
        # Test initial setup to ensure it calls the device methods correctly while missing a mode
        settings = {
            "alias": "keithley",
            "mode": "NULL",
            "output": True,
            "current": None,
            "voltage": None,
        }
        Keithley2400 = InstrumentFactory.get(InstrumentName.KEITHLEY2400)
        instrument = Keithley2400(settings=settings)
        instrument.device = mock.Mock()

        error_string = re.escape("Mode has to be either CURR (current) or Volt (voltage).")
        with pytest.raises(ValueError, match=error_string):
            instrument.initial_setup()

    def test_turn_on(self, keithley2400_curr_mode):
        # Placeholder test for the turn_on method, which could involve more device actions
        keithley2400_curr_mode.turn_on()
        # Add assertions if turn_on has real behavior in the future

    def test_turn_off(self, keithley2400_curr_mode):
        # Placeholder test for the turn_off method, which could involve more device actions
        keithley2400_curr_mode.turn_off()
        # Add assertions if turn_off has real behavior in the future

    def test_reset(self, keithley2400_curr_mode):
        # Test reset method to ensure it calls device.reset
        keithley2400_curr_mode.reset()
        keithley2400_curr_mode.device.reset.assert_called_once()

    def test_fast_sweep_current_mode(self, keithley2400_curr_mode):
        # Mock the fast sweep return data
        keithley2400_curr_mode.device.volt.return_value = 1.0

        data_sweep = [0.0, 0.5, 1.0]
        time_interval = 0.5

        dtype, times, measured = keithley2400_curr_mode.fast_sweep(data_sweep, time_interval)

        assert dtype == "Voltage (V)"
        assert len(times) == len(data_sweep)
        assert np.all(measured == 1.0)

    def test_fast_sweep_voltage_mode(self, keithley2400_volt_mode):
        # Mock the fast sweep return data
        keithley2400_volt_mode.device.curr.return_value = 1.0

        data_sweep = [0.0, 0.5, 1.0]
        time_interval = 0.5

        dtype, times, measured = keithley2400_volt_mode.fast_sweep(data_sweep, time_interval)

        assert dtype == "Current (A)"
        assert len(times) == len(data_sweep)
        assert np.all(measured == 1.0)

    def test_current_getter_curr_mode(self, keithley2400_curr_mode):
        # Test current getter in CURR mode
        keithley2400_curr_mode.settings.current = 1e-3
        assert keithley2400_curr_mode.current == 1e-3

    def test_current_getter_volt_mode(self, keithley2400_volt_mode):
        # Test current getter in VOLT mode
        keithley2400_volt_mode.device.curr.return_value = 2e-6
        assert keithley2400_volt_mode.current == 2e-6
        keithley2400_volt_mode.device.curr.assert_called_once()

    def test_current_setter_curr_mode(self, keithley2400_curr_mode):
        # Test current setter in CURR mode
        keithley2400_curr_mode.current = 5e-3
        assert keithley2400_curr_mode.settings.current == 5e-3
        keithley2400_curr_mode.device.curr.assert_called_with(5e-3)

    def test_current_setter_volt_mode_raises(self, keithley2400_volt_mode):
        # Test current setter raises error in VOLT mode
        error_string = "VOLTage mode set but current given."
        with pytest.raises(ValueError, match=error_string):
            keithley2400_volt_mode.current = 1e-3

    def test_voltage_getter_volt_mode(self, keithley2400_volt_mode):
        # Test voltage getter in VOLT mode
        keithley2400_volt_mode.settings.voltage = 1.25
        assert keithley2400_volt_mode.voltage == 1.25

    def test_voltage_getter_curr_mode(self, keithley2400_curr_mode):
        # Test voltage getter in CURR mode
        keithley2400_curr_mode.device.volt.return_value = 0.95
        assert keithley2400_curr_mode.voltage == 0.95
        keithley2400_curr_mode.device.volt.assert_called_once()

    def test_voltage_setter_volt_mode(self, keithley2400_volt_mode):
        # Test voltage setter in VOLT mode
        keithley2400_volt_mode.voltage = 2.5
        assert keithley2400_volt_mode.settings.voltage == 2.5
        keithley2400_volt_mode.device.volt.assert_called_with(2.5)

    def test_voltage_setter_curr_mode_raises(self, keithley2400_curr_mode):
        # Test voltage setter raises in CURR mode
        error_string = "CURRent mode set but voltage given."
        with pytest.raises(ValueError, match=error_string):
            keithley2400_curr_mode.voltage = 1.0