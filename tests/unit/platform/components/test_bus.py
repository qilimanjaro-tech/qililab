import pytest

from qililab.platform import Bus, Buses, Schema
from qililab.typings import Category

from ...data import MockedSettingsHashTable


@pytest.fixture(name="bus")
def fixture_bus() -> Bus:
    """Load Bus.

    Returns:
        Bus: Instance of the Bus class.
    """
    schema_settings = MockedSettingsHashTable.get(Category.SCHEMA.value)
    bus_dict = schema_settings["buses"][0]
    bus_settings = Bus.BusSettings(**bus_dict)

    return Bus(settings=bus_settings)


@pytest.fixture(name="buses")
def fixture_buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    schema = Schema(MockedSettingsHashTable.get(Category.SCHEMA.value))
    return Buses(buses=schema.buses)


class TestBus:
    """Unit tests checking the Bus attributes and methods."""

    def test_id_property(self, bus: Bus):
        """Test id property."""
        assert bus.id_ == bus.settings.id_

    def test_name_property(self, bus: Bus):
        """Test name property."""
        assert bus.name == bus.settings.name

    def test_category_property(self, bus: Bus):
        """Test name property."""
        assert bus.category == bus.settings.category

    def test_elements_property(self, bus: Bus):
        """Test elements property."""
        assert bus.elements == bus.settings.elements

    def test_signal_generator_property(self, bus: Bus):
        """Test signal_generator property."""
        assert bus.signal_generator == bus.settings.signal_generator

    def test_mixer_property(self, bus: Bus):
        """Test mixer property."""
        assert bus.mixer == bus.settings.mixer

    def test_resonator_property(self, bus: Bus):
        """Test resonator property."""
        assert bus.resonator == bus.settings.resonator

    def test_qubit_instrument_property(self, bus: Bus):
        """Test qubit_instrument property."""
        assert bus.qubit_instrument == bus.settings.qubit_instrument

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ and __getitem__ magic methods."""
        for idx, element in enumerate(bus):
            assert element == bus[idx]


class TestBuses:
    """Unit tests checking the Buses attributes and methods."""

    def test_add_method(self, buses: Buses, bus: Bus):
        """Test add method."""
        buses.add(bus=bus)
        assert buses[-1] == bus

    def test_iter_and_getitem_methods(self, buses: Buses):
        """Test __iter__ and __getitem__ methods."""
        for bus_idx, bus in enumerate(buses):
            for element_idx, element in enumerate(bus):
                assert buses[bus_idx][element_idx] == element
