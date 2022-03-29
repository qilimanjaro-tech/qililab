from dataclasses import dataclass

from qililab.platforms import Platform


@dataclass
class PlatformBuilder:
    """Builder of platform objects."""

    def build(self, name: str) -> Platform:
        """Build platform.

        Args:
            name (str): Name of the platform.

        Returns:
            Platform: Platform object describing the setup used.
        """
        return Platform(name)
