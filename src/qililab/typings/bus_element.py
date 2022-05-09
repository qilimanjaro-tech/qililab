"""BusElement class"""
from qililab.typings.enums import BusElementName
from qililab.typings.settings import SettingsType


class BusElement:
    """Class BusElement. All bus element classes must inherit from this class."""

    name: BusElementName
    settings: SettingsType

    def set_parameter(self, name: str, value: float):
        """Redirect __setattr__ magic method."""
        setattr(self.settings, name, value)
