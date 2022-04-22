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
    def num_buses(self) -> int:
        """
        Returns:
            int: Number of buses in the platform.
        """
        return len(self.settings.buses)

    def draw(self) -> None:
        """Draw schema."""
        for idx, bus in enumerate(self.settings.buses):
            print(f"Bus {idx}:\t", end="------")
            for element in bus:
                print(f"|{element.settings.name}_{element.settings.id_}", end="|------")
            print()

    def to_dict(self):
        """Return a dict representation of the Schema class."""
        return self.settings.to_dict()
