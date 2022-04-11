"""Schema class"""
from dataclasses import dataclass, field
from typing import Dict

from qililab.settings.schema import SchemaSettings


@dataclass
class Schema:
    """Class representing the schema of the platform.

    Args:
        settings (SchemaSettings): Settings that define the schema of the platform.
        buses (List[Dict[str, str]]): List of dictionaries that describe the category
        and names of the elements located in each bus.
    """

    settings: SchemaSettings
    buses: Dict[str, Dict[str, str]] = field(init=False)

    def __post_init__(self) -> None:
        """Post init method"""
        self.buses = self.settings.buses

    @property
    def num_buses(self) -> int:
        """
        Returns:
            int: Number of buses in the platform.
        """
        return len(self.buses)

    def draw(self) -> None:
        """Draw schema."""
        # TODO: Improve drawing
        for idx, bus in enumerate(self.buses.values()):
            print(f"Bus {idx}:\t", end="------")
            for _, element in bus.items():
                print(f"|{element}", end="|------")
            print()
