"""Tests for the Keithley2600 class."""
import pytest

from qililab.instruments import Keithley2600
from qililab.typings import Parameter


class TestKeithley2600:
    """Unit tests checking the Keithley2600 attributes and methods."""

    def test_id_property(self, keithley_2600_no_device: Keithley2600):
        """Test id property."""
        assert keithley_2600_no_device.id_ == keithley_2600_no_device.settings.id_

    def test_category_property(self, keithley_2600_no_device: Keithley2600):
        """Test category property."""
        assert keithley_2600_no_device.category == keithley_2600_no_device.settings.category

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.01), (Parameter.MAX_VOLTAGE, 19.0)])
    def test_setup_method_current_parameter(self, parameter: Parameter, value: float, keithley_2600: Keithley2600):
        """Test setup method."""
        keithley_2600.setup(parameter=parameter, value=value)
        if parameter == Parameter.CURRENT:
            assert keithley_2600.settings.max_current == value
        if parameter == Parameter.VOLTAGE:
            assert keithley_2600.settings.max_voltage == value

    def test_initial_setup_method(self, keithley_2600: Keithley2600):
        """Test initial_setup method."""
        keithley_2600.initial_setup()

    def test_turn_on_method(self, keithley_2600: Keithley2600):
        """Test turn_on method."""
        keithley_2600.turn_on()

    def test_turn_off_method(self, keithley_2600: Keithley2600):
        """Test turn_off method."""
        keithley_2600.turn_off()

    def test_reset_method(self, keithley_2600: Keithley2600):
        """Test reset method."""
        keithley_2600.reset()

    def test_fast_sweep_method(self, keithley_2600: Keithley2600):
        """Test fast_sweep method."""
        keithley_2600.fast_sweep(start=0, stop=1, steps=10, mode="VI")
