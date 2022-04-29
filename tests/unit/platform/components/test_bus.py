from typing import List

import pytest

from qililab.platform import Bus, BusControl, Buses, BusReadout
from qililab.typings import Category
from qililab.typings.enums import BusTypes, YAMLNames

from ...data import MockedSettingsHashTable


def load_buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    schema_settings = MockedSettingsHashTable.get(Category.SCHEMA.value)
    buses_settings: List[BusReadout | BusControl] = []
    for bus_settings in schema_settings[YAMLNames.BUSES.value]:
        if bus_settings[YAMLNames.NAME.value] == BusTypes.BUS_CONTROL.value:
            buses_settings.append(BusControl(bus_settings))
        elif bus_settings[YAMLNames.NAME.value] == BusTypes.BUS_READOUT.value:
            buses_settings.append(BusReadout(bus_settings))

    return Buses(buses=buses_settings)


@pytest.mark.parametrize("bus", [load_buses().buses[0], load_buses().buses[1]])
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

    def test_mixer_up_property(self, bus: Bus):
        """Test mixer_up property."""
        assert bus.mixer_up == bus.settings.mixer_up

    def test_resonator_property(self, bus: Bus):
        """Test resonator property."""
        if isinstance(bus, BusReadout):
            assert bus.resonator == bus.settings.resonator

    def test_qubit_property(self, bus: Bus):
        """Test qubit property."""
        if isinstance(bus, BusControl):
            assert bus.qubit == bus.settings.qubit

    def test_qubit_instrument_property(self, bus: Bus):
        """Test qubit_instrument property."""
        assert bus.qubit_instrument == bus.settings.qubit_instrument

    def test_iter_and_getitem_methods(self, bus: Bus):
        """Test __iter__ and __getitem__ magic methods."""
        for idx, element in enumerate(bus):
            assert element == bus[idx]


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
            for element_idx, element in enumerate(bus):
                assert buses[bus_idx][element_idx] == element
