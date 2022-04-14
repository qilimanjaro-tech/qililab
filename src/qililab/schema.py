"""Schema class"""
from qililab.settings.schema import SchemaSettings


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
        # TODO: Improve drawing
        for idx, bus in enumerate(self.settings.buses.values()):
            print(f"Bus {idx}:\t", end="------")
            for _, element in bus.items():
                print(f"|{element}", end="|------")
            print()
