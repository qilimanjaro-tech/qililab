"""Tests for the Bus class."""
from types import NoneType

import pytest

from qililab.instruments import SystemControl
from qililab.platform import Bus, BusControl, Buses, BusReadout, Qubit, Resonator

from ....conftest import buses as load_buses


@pytest.mark.parametrize("bus", [load_buses().buses[0], load_buses().buses[1]])
class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_system_control_instance(self, bus: Bus):
        """Test system_control instance."""
        assert isinstance(bus.system_control, SystemControl)

    def test_resonator_instance(self, bus: Bus):
        """Test resonator instance."""
        if isinstance(bus, BusReadout):
            assert isinstance(bus.resonator, Resonator)

    def test_qubit_instance(self, bus: Bus):
        """Test qubit instance."""
        if isinstance(bus, BusControl):
            assert isinstance(bus.qubit, Qubit)

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ magic method."""
        for element in bus:
            assert not isinstance(element, (NoneType, str))


@pytest.mark.parametrize("buses", [load_buses()])
@pytest.mark.parametrize("bus", [load_buses().buses[0]])
class TestBuses:
    """Unit tests checking the Buses attributes and methods."""

    def test_add_method(self, buses: Buses, bus: BusControl | BusReadout):
        """Test add method."""
        buses.add(bus=bus)
        assert buses[-1] == bus

    def test_iter_and_getitem_methods(self, buses: Buses, bus: Bus):
        """Test __iter__, and __getitem__ methods."""
        for bus_idx, bus in enumerate(buses):
            assert buses[bus_idx] == bus

    def test_len_method(self, buses: Buses, bus: Bus):
        """Test __len__ method."""
        assert len(buses) == len(buses.buses)
