"""Tests for the Buses class."""
import pytest

from qililab.platform import Bus, Buses

from .aux_methods import buses as load_buses


@pytest.mark.parametrize("buses", [load_buses()])
class TestBuses:
    """Unit tests checking the Buses attributes and methods."""

    @pytest.mark.parametrize("bus", [load_buses().elements[0]])
    def test_add_method(self, buses: Buses, bus: Bus):
        """Test add method."""
        buses.add(bus=bus)
        assert buses[-1] == bus

    def test_iter_and_getitem_methods(self, buses: Buses):
        """Test __iter__, and __getitem__ methods."""
        for bus_idx, bus in enumerate(buses):
            assert buses[bus_idx] == bus  # pylint: disable=unnecessary-list-index-lookup

    def test_len_method(self, buses: Buses):
        """Test __len__ method."""
        assert len(buses) == len(buses.elements)
