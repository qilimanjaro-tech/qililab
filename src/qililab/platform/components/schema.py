"""Schema class"""
from dataclasses import asdict

from qililab.platform.utils.enum_dict_factory import enum_dict_factory
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
                print(f"|{element.name}_{element.id_}", end="|------")
            print()

    def to_dict(self):
        """Return all Schema information as a dictionary."""
        return asdict(self.settings, dict_factory=enum_dict_factory)
