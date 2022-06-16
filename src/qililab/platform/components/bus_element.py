"""BusElement class"""
from qililab.settings import Settings
from qililab.typings.enums import Parameter
from qililab.typings.factory_element import FactoryElement


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: Settings

    def set_parameter(self, parameter: Parameter | str, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        if isinstance(parameter, Parameter):
            parameter = parameter.value
        self.settings.set_parameter(name=parameter, value=value)
