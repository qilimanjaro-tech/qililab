from types import NoneType

import pytest

from qililab.instruments import Mixer, QubitInstrument, SignalGenerator
from qililab.platform import (
    PLATFORM_MANAGER_YAML,
    Bus,
    BusControl,
    Buses,
    BusReadout,
    Qubit,
    Resonator,
)
from qililab.typings import Category

from ...data import MockedSettingsHashTable


def load_buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    schema_settings = MockedSettingsHashTable.get(Category.SCHEMA.value)

    return PLATFORM_MANAGER_YAML.build_schema(schema_settings=schema_settings).buses


@pytest.mark.parametrize("bus", [load_buses().buses[0], load_buses().buses[1]])
class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_category_instance(self, bus: Bus):
        """Test name instance."""
        assert isinstance(bus.readout, bool)

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
