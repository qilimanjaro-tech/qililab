"""BusElement class"""
from qililab.typings.enums import Parameter
from qililab.typings.factory_element import FactoryElement
from qililab.typings.settings import SettingsType


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: SettingsType

    def set_parameter(self, parameter: Parameter | str, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        if isinstance(parameter, Parameter):
            parameter = parameter.value
        self.settings.set_parameter(name=parameter, value=value)
