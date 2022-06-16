"""Tests for the Bus class."""
from types import NoneType

import pytest

from qililab.instruments import SystemControl
from qililab.platform import Bus, Qubit, Resonator
from qililab.typings import BusSubcategory

from ....conftest import buses as load_buses


@pytest.mark.parametrize("bus", [load_buses().elements[0], load_buses().elements[1]])
class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_system_control_instance(self, bus: Bus):
        """Test system_control instance."""
        assert isinstance(bus.system_control, SystemControl)

    def test_target_instance(self, bus: Bus):
        """Test resonator instance."""
        if bus.subcategory == BusSubcategory.READOUT:
            assert isinstance(bus.port, Resonator)

    def test_qubit_instance(self, bus: Bus):
        """Test qubit instance."""
        if bus.subcategory == BusSubcategory.CONTROL:
            assert isinstance(bus.port, Qubit)

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ magic method."""
        for element in bus:
            assert not isinstance(element, (NoneType, str))
