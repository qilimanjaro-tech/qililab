"""Tests for the SystemControl class."""
from qililab.platform.components.bus_element import BusElement
from qililab.system_control import SystemControl


class TestSystemControl:
    """Unit tests checking the SystemControl attributes and methods"""

    def test_iter_method(self, base_system_control: SystemControl):
        """Test __iter__ method."""
        for name, value in base_system_control:
            assert isinstance(name, str)
            assert isinstance(value, BusElement)

    def test_category_property(self, base_system_control: SystemControl):
        """Test category property."""
        assert base_system_control.category == base_system_control.settings.category

    def test_system_control_category_property(self, base_system_control: SystemControl):
        """Test system_control_category property."""
        assert base_system_control.system_control_category == base_system_control.settings.system_control_category

    def test_system_control_subcategory_property(self, base_system_control: SystemControl):
        """Test system_control_subcategory property."""
        assert base_system_control.system_control_subcategory == base_system_control.settings.system_control_subcategory

    def test_name_property(self, base_system_control: SystemControl):
        """Test name property."""
        assert base_system_control.name.value == (
            f"{base_system_control.system_control_category.value}_"
            + f"{base_system_control.system_control_subcategory.value}_{base_system_control.category.value}"
        )

    def test_id_property(self, base_system_control: SystemControl):
        """Test id property."""
        assert base_system_control.id_ == base_system_control.settings.id_
