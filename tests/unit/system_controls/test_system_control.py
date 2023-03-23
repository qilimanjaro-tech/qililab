"""Tests for the SystemControl class."""
from qililab.instruments import Instrument
from qililab.system_control import SystemControl


class TestSystemControl:
    """Unit tests checking the SystemControl attributes and methods"""

    def test_iter_method(self, base_system_control: SystemControl):
        """Test __iter__ method."""
        for instrument in base_system_control:
            assert isinstance(instrument, Instrument)

    def test_category_property(self, base_system_control: SystemControl):
        """Test category property."""
        assert base_system_control.category == base_system_control.settings.category

    def test_name_property(self, base_system_control: SystemControl):
        """Test name property."""
        assert base_system_control.name.value == "system_control"

    def test_id_property(self, base_system_control: SystemControl):
        """Test id property."""
        assert base_system_control.id_ == base_system_control.settings.id_
