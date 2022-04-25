"""Schema class"""
from dataclasses import dataclass
from typing import List

from qililab.platform.components.bus import Bus
from qililab.settings import Settings
from qililab.typings import SchemaDrawOptions


class Schema:
    """Class representing the schema of the platform.

    Args:
        settings (SchemaSettings): Settings that define the schema of the platform.
    """

    @dataclass
    class SchemaSettings(Settings):
        """Schema settings.

        Args:
            buses (BusesSettings): List containing the settings of the elements for each bus.
        """

        buses: List[Bus.BusSettings]

        def __post_init__(self):
            """Cast the settings of each element to the Settings class."""
            super().__post_init__()
            self.buses = [Bus.BusSettings(**bus_settings) for bus_settings in self.buses]

        def to_dict(self):
            """Return a dict representation of the SchemaSettings class."""
            return {
                "id_": self.id_,
                "name": self.name,
                "category": self.category.value,
                "buses": [bus.to_dict() for bus in self.buses],
            }

    def __init__(self, settings: dict):
        self.settings = self.SchemaSettings(**settings)

    @property
    def id_(self):
        """Schema 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Schema 'name' property.

        Returns:
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Schema 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def buses(self):
        """Schema 'buses' property.

        Returns:
            List[BusSettings]: settings.buses.
        """
        return self.settings.buses

    def draw(self, options: SchemaDrawOptions) -> None:
        """Draw schema.

        Args:
            options (SchemaDrawOptions): Method to generate the drawing.
        """
        if options == SchemaDrawOptions.PRINT:
            for idx, bus in enumerate(self.buses):
                print(f"Bus {idx}:\t", end="------")
                for element in bus:
                    print(f"|{element.name}_{element.id_}", end="|------")
                print()
        elif options == SchemaDrawOptions.FILE:
            raise NotImplementedError("This function is not implemented yet.")

    def to_dict(self):
        """Return a dict representation of the Schema class."""
        return self.settings.to_dict()
