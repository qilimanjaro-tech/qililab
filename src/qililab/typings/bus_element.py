"""BusElement class"""
from qililab.typings.factory_element import FactoryElement
from qililab.typings.settings import SettingsType


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: SettingsType

    def set_parameter(self, name: str, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        self.settings.set_parameter(name=name, value=value)
