"""Schema class"""
from qililab.settings.platform.components.schema import SchemaSettings


class Schema:
    """Class representing the schema of the platform.

    Args:
        settings (SchemaSettings): Settings that define the schema of the platform.
    """

    def __init__(self, settings: dict):
        self.settings = SchemaSettings(**settings)

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

    def draw(self) -> None:
        """Draw schema."""
        for idx, bus in enumerate(self.buses):
            print(f"Bus {idx}:\t", end="------")
            for element in bus:
                print(f"|{element.name}_{element.id_}", end="|------")
            print()

    def to_dict(self):
        """Return a dict representation of the Schema class."""
        return self.settings.to_dict()
