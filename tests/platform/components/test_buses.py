"""Tests for the Buses class."""
import pytest

from qililab.platform import Bus, Buses
from qililab.system_control import ReadoutSystemControl

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

    def test_readout_buses(self, buses: Buses):
        """Test that the ``readout_buses`` method returns a list of readout buses."""
        readout_buses = buses.readout_buses
        assert isinstance(readout_buses, list)
        assert isinstance(readout_buses[0].system_control, ReadoutSystemControl)

    def test_str_method(self, buses: Buses):
        """Test print buses."""
        assert str(buses) == "\n".join(str(bus) for bus in buses.elements)
