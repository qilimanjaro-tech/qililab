"""Tests for the Bus class."""
from types import NoneType

import pytest

from qililab.platform import Bus
from qililab.system_controls import SystemControl

from .aux_methods import buses as load_buses


@pytest.mark.parametrize("bus", [load_buses().elements[0], load_buses().elements[1]])
class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_system_control_instance(self, bus: Bus):
        """Test system_control instance."""
        assert isinstance(bus.system_control, SystemControl)

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ magic method."""
        for element in bus:
            assert not isinstance(element, (NoneType, str))

    def test_print_bus(self, bus: Bus):
        """Test print bus."""
        print(bus)
