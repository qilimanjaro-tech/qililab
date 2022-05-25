"""Tests for the Buses class."""
import pytest

from qililab.platform import Bus, BusControl, Buses, BusReadout

from ....conftest import buses as load_buses


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
