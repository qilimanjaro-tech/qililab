from typing import List

import pytest

from qililab.platform import BusControl, Buses, BusReadout, Schema
from qililab.typings import BusTypes, Category, SchemaDrawOptions, YAMLNames

from ...data import MockedSettingsHashTable


@pytest.fixture(name="schema")
def fixture_schema() -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    schema_settings = MockedSettingsHashTable.get(Category.SCHEMA.value)
    buses_settings: List[BusReadout | BusControl] = []
    for bus_settings in schema_settings[YAMLNames.BUSES.value]:
        if bus_settings[YAMLNames.NAME.value] == BusTypes.BUS_CONTROL.value:
            buses_settings.append(BusControl(bus_settings))
        elif bus_settings[YAMLNames.NAME.value] == BusTypes.BUS_READOUT.value:
            buses_settings.append(BusReadout(bus_settings))

    return Schema(buses=Buses(buses=buses_settings))


class Testschema:
    """Unit tests checking the Schema attributes and methods."""

    def test_asdict_method(self, schema: Schema):
        """Test schema schema asdict method."""
        assert isinstance(schema.to_dict(), dict)

    def test_draw_method_print(self, schema: Schema):
        """Test schema schema draw method."""
        schema.draw(options=SchemaDrawOptions.PRINT)

    def test_draw_method__file(self, schema: Schema):
        """Test schema schema draw method raise error."""
        with pytest.raises(NotImplementedError):
            schema.draw(options=SchemaDrawOptions.FILE)
