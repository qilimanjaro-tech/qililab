from types import NoneType
from unittest.mock import patch

import pytest

from qililab.instruments import Mixer, QubitInstrument, SignalGenerator
from qililab.platform import (
    PLATFORM_MANAGER_DB,
    Bus,
    BusControl,
    Buses,
    BusReadout,
    Qubit,
    Resonator,
)

from ...utils.side_effect import yaml_safe_load_side_effect


def load_buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")
        mock_load.assert_called()
    return platform.buses


@pytest.mark.parametrize("bus", [load_buses().buses[0], load_buses().buses[1]])
class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_signal_generator_instance(self, bus: Bus):
        """Test signal_generator instance."""
        assert isinstance(bus.signal_generator, SignalGenerator)

    def test_mixer_up_instance(self, bus: Bus):
        """Test mixer_up instance."""
        assert isinstance(bus.mixer_up, Mixer)

    def test_resonator_instance(self, bus: Bus):
        """Test resonator instance."""
        if isinstance(bus, BusReadout):
            assert isinstance(bus.resonator, Resonator)

    def test_qubit_instance(self, bus: Bus):
        """Test qubit instance."""
        if isinstance(bus, BusControl):
            assert isinstance(bus.qubit, Qubit)

    def test_qubit_instrument_instance(self, bus: Bus):
        """Test qubit_instrument instance."""
        assert isinstance(bus.qubit_instrument, QubitInstrument)

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ magic method."""
        for element in bus:
            assert not isinstance(element, (NoneType, str))


@pytest.mark.parametrize("buses", [load_buses()])
@pytest.mark.parametrize("bus", [load_buses().buses[0]])
class TestBuses:
    """Unit tests checking the Buses attributes and methods."""

    def test_add_method(self, buses: Buses, bus: BusReadout | BusControl):
        """Test add method."""
        buses.add(bus=bus)
        assert buses[-1] == bus

    def test_iter_and_getitem_methods(self, buses: Buses, bus: Bus):
        """Test __iter__ and __getitem__ methods."""
        for bus_idx, bus in enumerate(buses):
            assert buses[bus_idx] == bus
