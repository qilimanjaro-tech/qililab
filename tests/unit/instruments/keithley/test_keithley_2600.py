"""Tests for the Keithley2600 class."""
from qililab.instruments import Keithley2600


class TestKeithley2600:
    """Unit tests checking the Keithley2600 attributes and methods."""

    def test_id_property(self, keithley_2600: Keithley2600):
        """Test id property."""
        assert keithley_2600.id_ == keithley_2600.settings.id_

    def test_category_property(self, keithley_2600: Keithley2600):
        """Test category property."""
        assert keithley_2600.category == keithley_2600.settings.category

    def test_reset_method(self, keithley_2600: Keithley2600):
        """Test reset method."""
        keithley_2600.reset()

    def test_fast_sweep_method(self, keithley_2600: Keithley2600):
        """Test fast_sweep method."""
        keithley_2600.fast_sweep(start=0, stop=1, steps=10, mode="VI")
