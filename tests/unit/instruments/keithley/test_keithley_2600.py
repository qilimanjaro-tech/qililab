"""Tests for the Keithley2600 class."""
from qililab.instruments import Keithley2600


class TestKeithley2600:
    """Unit tests checking the Keithley2600 attributes and methods."""

    def test_id_property(self, keithley_2600_no_device: Keithley2600):
        """Test id property."""
        assert keithley_2600_no_device.id_ == keithley_2600_no_device.settings.id_

    def test_category_property(self, keithley_2600_no_device: Keithley2600):
        """Test category property."""
        assert keithley_2600_no_device.category == keithley_2600_no_device.settings.category

    def test_setup_method(self, keithley_2600: Keithley2600):
        """Test setup method."""
        keithley_2600.setup()

    def test_initial_setup_method(self, keithley_2600: Keithley2600):
        """Test initial_setup method."""
        keithley_2600.initial_setup()

    def test_start_method(self, keithley_2600: Keithley2600):
        """Test start method."""
        keithley_2600.start()

    def test_stop_method(self, keithley_2600: Keithley2600):
        """Test stop method."""
        keithley_2600.stop()

    def test_reset_method(self, keithley_2600: Keithley2600):
        """Test reset method."""
        keithley_2600.reset()

    def test_fast_sweep_method(self, keithley_2600: Keithley2600):
        """Test fast_sweep method."""
        keithley_2600.fast_sweep(start=0, stop=1, steps=10, mode="VI")
