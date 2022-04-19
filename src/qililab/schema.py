"""Schema class"""
from dataclasses import asdict

from qililab.settings.schema import SchemaSettings
from qililab.typings import dict_factory


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
                print(f"|{element.name}_{element.id_}", end="|------")
            print()

    def asdict(self):
        """Return all Schema information as a dictionary."""
        return asdict(self.settings, dict_factory=dict_factory)
